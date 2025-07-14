import logging
from odoo import models, _

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self):
        """
        Override button_start to detect MO state changes and send API
        """
        # Check state BEFORE starting
        for workorder in self:
            production = workorder.production_id
            # Check if this is a Sub MO
            main_mo = production._find_main_mo(production)
            if main_mo.id != production.id:  # This is a Sub MO
                old_state = production.state
                
                # Check if this is the FIRST work operation to start (confirmed → in_progress)
                if old_state == 'confirmed':
                    production._send_sub_mo_api('started')
        
        # Call parent method to actually start
        return super().button_start()

    def button_finish(self):
        """
        Override button_finish to detect when all work operations are done
        """
        # Call parent method first to actually finish
        result = super().button_finish()
        
        # Check state AFTER finishing
        for workorder in self:
            production = workorder.production_id
            # Check if this is a Sub MO
            main_mo = production._find_main_mo(production)
            if main_mo.id != production.id:  # This is a Sub MO
                current_state = production.state
                
                # Check if ALL work orders are now finished (MO should be done or to_close)
                all_workorders_done = all(wo.state in ['done', 'cancel'] for wo in production.workorder_ids)
                
                if all_workorders_done and current_state in ['done', 'to_close']:
                    production._send_sub_mo_api('completed')
        
        return result 