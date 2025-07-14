import json
import logging
import requests
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Cache to prevent duplicate API calls
    _api_call_cache = {}

    def _ensure_default_parameters(self):
        """Ensure default system parameters exist"""
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        
        # Default parameters
        default_params = {
            'mrp_work_operation_api.enabled': 'True',
            'mrp_work_operation_api.php_endpoint_url': 'http://host.docker.internal:8080/api/test_php_endpoint.php',
            'mrp_work_operation_api.api_timeout': '10'
        }
        
        for key, default_value in default_params.items():
            if not IrConfigParameter.get_param(key):
                IrConfigParameter.set_param(key, default_value)
                _logger.info(f"Set default parameter: {key} = {default_value}")

    def _get_php_api_url(self):
        """Get the PHP API endpoint URL from system parameters"""
        self._ensure_default_parameters()
        return self.env['ir.config_parameter'].sudo().get_param(
            'mrp_work_operation_api.php_endpoint_url', 
            default='http://host.docker.internal:8080/api/test_php_endpoint.php'
        )

    def _find_main_mo(self, mo):
        """
        Find the main/parent Manufacturing Order from a sub MO
        """
        # Method 1: Check if this MO has an origin that looks like another MO
        if mo.origin:
            parent_mo = self.env['mrp.production'].search([
                ('name', '=', mo.origin)
            ], limit=1)
            
            if parent_mo:
                # Recursively check if this parent has another parent
                if parent_mo.origin and parent_mo.origin != mo.origin:
                    return self._find_main_mo(parent_mo)
                else:
                    return parent_mo
        
        # Method 2: Check through procurement group for related MOs
        if mo.procurement_group_id:
            related_mos = self.env['mrp.production'].search([
                ('procurement_group_id', '=', mo.procurement_group_id.id),
                ('id', '!=', mo.id)  # Exclude current MO
            ])
            
            for related_mo in related_mos:
                # Look for MO without origin (likely main MO)
                if not related_mo.origin:
                    return related_mo
                
                # Look for MO that is not originated from another MO
                if related_mo.origin and not related_mo.origin.startswith('MO/'):
                    return related_mo
        
        # Method 3: Check through stock moves (move_dest_ids relationship)
        if mo.move_finished_ids:
            for move in mo.move_finished_ids:
                if move.move_dest_ids:
                    for dest_move in move.move_dest_ids:
                        if dest_move.production_id and dest_move.production_id.id != mo.id:
                            potential_main_mo = dest_move.production_id
                            
                            # Check if this could be the main MO
                            if not potential_main_mo.origin:
                                return potential_main_mo
        
        # Method 4: Try to find by name pattern (if sub MOs follow a pattern)
        if '-' in mo.name:
            base_name_parts = mo.name.split('-')
            if len(base_name_parts) >= 3:
                potential_main_name = '-'.join(base_name_parts[:-1])
                
                potential_main_mo = self.env['mrp.production'].search([
                    ('name', '=', potential_main_name)
                ], limit=1)
                
                if potential_main_mo and potential_main_mo.id != mo.id:
                    return potential_main_mo
        
        # Method 5: Look for Sales Order origin
        if mo.origin and not mo.origin.startswith('MO/'):
            same_origin_mos = self.env['mrp.production'].search([
                ('origin', '=', mo.origin),
                ('id', '!=', mo.id)
            ])
            
            for origin_mo in same_origin_mos:
                # Look for the one that might be the main (typically created first)
                if origin_mo.create_date <= mo.create_date:
                    return origin_mo
        
        # If all methods fail, return the original MO
        return mo

    @api.model
    def create(self, vals):
        """
        Override create to detect new Sub MO creation
        """
        result = super().create(vals)
        return result

    def write(self, vals):
        """
        Override write to detect Sub MO state changes
        """
        result = super().write(vals)
        return result

    def button_mark_done(self):
        """
        Override button_mark_done - DISABLED API calls (using write() method instead)
        """
        return super().button_mark_done()

    def _prepare_api_data(self, status):
        """
        Prepare the data payload for the PHP API (Sub MO version)
        
        Args:
            status (str): 'started' or 'completed'
            
        Returns:
            dict: API payload data
        """
        # Ensure we're working with a single record
        self.ensure_one()
        
        # This MO is the Sub MO
        sub_mo = self
        
        # Find the main MO (parent MO)
        main_mo = self._find_main_mo(sub_mo)
        
        # Use the main MO's name as knockdown_no (strip whitespace)
        knockdown_no = main_mo.name.strip() if main_mo.name else ''
        
        # Get station_name from Sub MO product internal reference (default_code)
        product = sub_mo.product_id
        if product and product.default_code:
            station_name = product.default_code
        else:
            # Fallback to product name if no internal reference
            station_name = product.name if product else 'Unknown Product'
        
        # Prepare timestamps with status based on API call type
        start_time_obj = {
            'time': None,
            'status': False
        }
        end_time_obj = {
            'time': None,
            'status': False
        }
        
        if status == 'started':
            # For "started" API: record start_time as current time
            start_time_obj = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': True
            }
            # end_time remains null for "started"
        elif status == 'completed':
            # For "completed" API: use stored start_time and current time as end_time
            if sub_mo.date_start:
                start_time_obj = {
                    'time': sub_mo.date_start.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': True
                }
            
            # Set end_time as current time for "completed"
            end_time_obj = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': True
            }
        
        api_data = {
            'knockdown_no': knockdown_no,
            'station_name': station_name,
            'start_time': start_time_obj,
            'end_time': end_time_obj,
            'status': status,
            'mo_id': main_mo.id,  # Main MO ID
            'sub_mo_id': sub_mo.id,  # Sub MO ID
            'sub_mo_name': sub_mo.name,  # Sub MO name
        }
        
        return api_data

    def _send_sub_mo_api(self, status):
        """
        Send API request for Sub MO state change
        
        Args:
            status (str): 'started' or 'completed'
        """
        try:
            api_data = self._prepare_api_data(status)
            
            # Check for duplicate calls
            start_time_str = api_data['start_time']['time'] if api_data['start_time']['status'] else 'null'
            end_time_str = api_data['end_time']['time'] if api_data['end_time']['status'] else 'null'
            timestamp_key = f"{start_time_str}_{end_time_str}_{status}"
            
            if self._is_duplicate_call(status, timestamp_key):
                return
            
            success, response = self._send_api_request(api_data)
            
            # Log API activity to MO's internal log
            self._log_api_activity(api_data, success, response)
                
        except Exception as e:
            _logger.error(f"❌ Error during Sub MO {status} API call: {str(e)}")
            # Log error to MO's internal log
            self._log_api_activity({'status': status, 'station_name': 'Unknown'}, False, None, str(e))

    def _log_api_activity(self, api_data, success, response, error_msg=None):
        """
        Log API activity to MO's internal log note
        
        Args:
            api_data (dict): The API data that was sent
            success (bool): Whether the API call was successful
            response (dict): The response from PHP API
            error_msg (str): Error message if any
        """
        try:
            # Prepare log message
            status_emoji = "✅" if success else "❌"
            status_thai = "เริ่มงาน" if api_data.get('status') == 'started' else "เสร็จงาน"
            
            if success:
                log_title = f"{status_emoji} API {status_thai} - ส่งข้อมูลสำเร็จ"
                
                # Create user-friendly summary
                user_info = []
                user_info.append(f"สถานี: {api_data.get('station_name', 'N/A')}")
                user_info.append(f"Knockdown No: {api_data.get('knockdown_no', 'N/A')}")
                user_info.append(f"สถานะ: {status_thai}")
                
                if api_data.get('start_time', {}).get('status'):
                    user_info.append(f"เวลาเริ่ม: {api_data['start_time']['time']}")
                
                if api_data.get('end_time', {}).get('status'):
                    user_info.append(f"เวลาเสร็จ: {api_data['end_time']['time']}")
                
                if response and response.get('log_id'):
                    user_info.append(f"Log ID: {response['log_id']}")
                
                user_summary = "\n".join(user_info)
                
                # Format JSON data for display
                json_data = json.dumps(api_data, ensure_ascii=False, indent=2)
                
                log_body = f"{log_title}\n\n{user_summary}\n\n" + "="*50 + "\nJSON ที่ส่งออกไป:\n" + "="*50 + f"\n{json_data}"
                
            else:
                log_title = f"{status_emoji} API {status_thai} - ส่งข้อมูลไม่สำเร็จ"
                
                user_info = []
                if api_data.get('station_name'):
                    user_info.append(f"สถานี: {api_data['station_name']}")
                user_info.append(f"เหตุผล: {error_msg or 'ไม่ทราบสาเหตุ'}")
                
                user_summary = "\n".join(user_info)
                
                # Show partial JSON data even for errors
                json_data = json.dumps(api_data, ensure_ascii=False, indent=2)
                
                log_body = f"{log_title}\n\n{user_summary}\n\n" + "="*50 + "\nJSON ที่พยายามส่ง:\n" + "="*50 + f"\n{json_data}"
            
            # Post message to MO's chatter
            self.message_post(
                body=log_body,
                subject=f"API Integration - {status_thai}",
                message_type='comment',
                subtype_xmlid='mail.mt_note'  # Internal note
            )
            
        except Exception as e:
            _logger.error(f"❌ Error logging API activity: {str(e)}")

    def _send_api_request(self, data):
        """
        Send HTTP POST request to the PHP API
        
        Args:
            data (dict): The data to send to the API
            
        Returns:
            tuple: (success: bool, response_data: dict or None)
        """
        api_url = self._get_php_api_url()
        if not api_url:
            _logger.error("🚫 PHP API URL not configured")
            return False, None
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Odoo-MRP-Integration/1.0'
        }
        
        try:
            _logger.info(f"📤 Sending {data['status']} API - {data['station_name']} - Data: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(
                api_url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    _logger.info(f"✅ {data['status']} API Success - Log ID: {response_data.get('log_id', 'N/A')}")
                    return True, response_data
                except json.JSONDecodeError:
                    _logger.error(f"❌ Invalid JSON response: {response.text}")
                    return False, None
            else:
                _logger.error(f"❌ API {data['status']} failed: {response.status_code} - {response.text}")
                return False, None
                
        except requests.exceptions.RequestException as e:
            _logger.error(f"❌ Network error: {str(e)}")
            return False, None



    def _get_cache_key(self, operation_type, timestamp_str):
        """Generate a unique cache key for API calls"""
        return f"{self.id}_{operation_type}_{timestamp_str}"
    
    def _is_duplicate_call(self, operation_type, timestamp_str):
        """Check if this API call was already sent recently"""
        cache_key = self._get_cache_key(operation_type, timestamp_str)
        current_time = datetime.now().timestamp()
        
        # Check if we sent this exact call in the last 5 seconds
        if cache_key in self._api_call_cache:
            last_call_time = self._api_call_cache[cache_key]
            if current_time - last_call_time < 5:  # 5 second window
                return True
        
        # Cache this call
        self._api_call_cache[cache_key] = current_time
        return False 