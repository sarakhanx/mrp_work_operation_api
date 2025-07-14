from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    php_api_endpoint_url = fields.Char(
        string='PHP API Endpoint URL',
        help='The URL of the PHP API endpoint to send work operation data to',
        config_parameter='mrp_work_operation_api.php_endpoint_url',
        default='http://localhost/api/work_operation.php'
    )
    
    php_api_timeout = fields.Integer(
        string='API Timeout (seconds)',
        help='Timeout for API requests in seconds',
        config_parameter='mrp_work_operation_api.api_timeout',
        default=10
    )
    
    php_api_enabled = fields.Boolean(
        string='Enable PHP API Integration',
        help='Enable sending work operation data to PHP API',
        config_parameter='mrp_work_operation_api.enabled',
        default=True
    ) 