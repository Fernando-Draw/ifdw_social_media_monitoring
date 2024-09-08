from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from pytz import timezone, utc
from odoo.http import request

class SmmonitorTaskAnalytics(models.Model):
    _name = 'project.task.smmonitor'
    _description = 'Análisis y control de RR.SS. en tareas de proyectos'

    task_id = fields.Many2one('project.task', string='Tarea', required=True, ondelete='cascade')
    date = fields.Date(string='Fecha', required=True)  # Quitamos default aquí
    engagement = fields.Float(string='Vinculación (%)', digits=(6,2))
    reach = fields.Integer(string='Alcance')
    interactions = fields.Integer(string='Interacciones (CTR)')
    impressions = fields.Integer(string='Impresiones')

    @api.model
    def save_tz_offset(self, offset):
        self.env['ir.config_parameter'].sudo().set_param('tz_offset', str(offset))

    @api.constrains('date', 'engagement', 'reach', 'interactions', 'impressions')
    def _check_values(self):
        for record in self:
            if record.date > fields.Date.today():
                raise ValidationError("La fecha no puede ser posterior al día de hoy.")
            if record.date < fields.Date.today() - timedelta(days=365):
                raise ValidationError("La fecha no puede ser anterior a un año desde hoy.")
            if record.engagement < 0 or record.engagement > 9999.99:
                raise ValidationError("La vinculación debe estar entre 0% y 9999.99%.")
            if record.reach < 0:
                raise ValidationError("El alcance no puede ser negativo.")
            if record.interactions < 0:
                raise ValidationError("Las interacciones no pueden ser negativas.")
            if record.impressions < 0:
                raise ValidationError("Las impresiones no pueden ser negativas.")

    @api.constrains('engagement', 'reach', 'interactions', 'impressions')
    def _check_not_all_zero(self):
        for record in self:
            if record.engagement == 0 and record.reach == 0 and record.interactions == 0 and record.impressions == 0:
                raise ValidationError("Al menos uno de los valores analíticos debe ser distinto de cero.")


class SmmonitorProjectTask(models.Model):
    _inherit = 'project.task'

    def save_tz_offset(self):
            #Guardar el desplazamiento de zona horaria en la configuración del sistema
            self.env['ir.config_parameter'].sudo().set_param('tz_offset', request.session.datetime.now().utcoffset().total_seconds() / 60)

    smmonitor_ids = fields.One2many('project.task.smmonitor', 'task_id', string='Análisis de RR.SS.')
    temp_date = fields.Date(string='Fecha', default=fields.Date.context_today)
    user_timezone_offset = fields.Integer(string='Desplazamiento zona horaria del usuario', default=0)
    temp_engagement = fields.Float(string='Vinculación (%)', digits=(6,2), default=0)
    temp_reach = fields.Integer(string='Alcance', default=0)
    temp_interactions = fields.Integer(string='Interacciones (CTR)', default=0)
    temp_impressions = fields.Integer(string='Impresiones', default=0)
    analytics_count = fields.Integer(string='Número de registros', compute='_compute_analytics_count')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'user_timezone_offset' in fields:
            tz_offset = request.httprequest.cookies.get('tz_offset')
            if tz_offset:
                res['user_timezone_offset'] = int(tz_offset)
        return res

    @api.depends('temp_engagement', 'temp_reach', 'temp_interactions', 'temp_impressions')
    def _compute_can_add_analytics(self):
        for task in self:
            task.can_add_analytics = any([
                task.temp_engagement != 0,
                task.temp_reach != 0,
                task.temp_interactions != 0,
                task.temp_impressions != 0
            ])
    
    @api.depends('smmonitor_ids')
    def _compute_analytics_count(self):
        for task in self:
            task.analytics_count = len(task.smmonitor_ids)

    can_add_analytics = fields.Boolean(compute='_compute_can_add_analytics')

    @api.constrains('temp_date', 'temp_engagement', 'temp_reach', 'temp_interactions', 'temp_impressions')
    def _check_temp_values(self):
        for task in self:
            today = fields.Date.today()

            if task.temp_date > fields.Date.today():
                raise ValidationError("La fecha no puede ser posterior al día de hoy.")
            if task.temp_date < fields.Date.today() - timedelta(days=365):
                raise ValidationError("La fecha no puede ser anterior a un año desde hoy.")
            if task.temp_engagement < 0 or task.temp_engagement > 9999.99:
                raise ValidationError("La vinculación debe estar entre 0% y 9999.99%.")
            if task.temp_reach < 0:
                raise ValidationError("El alcance no puede ser negativo.")
            if task.temp_interactions < 0:
                raise ValidationError("Las interacciones no pueden ser negativas.")
            if task.temp_impressions < 0:
                raise ValidationError("Las impresiones no pueden ser negativas.")

    def action_add_analytics(self):
        self.ensure_one()
        if self.can_add_analytics:
            self.env['project.task.smmonitor'].create({
                'task_id': self.id,
                'date': self.temp_date,
                'engagement': self.temp_engagement,
                'reach': self.temp_reach,
                'interactions': self.temp_interactions,
                'impressions': self.temp_impressions,
            })
            self.write({
                'temp_date': fields.Date.context_today(self),
                'temp_engagement': 0,
                'temp_reach': 0,
                'temp_interactions': 0,
                'temp_impressions': 0,
            })
        else:
            raise ValidationError("No se pueden agregar análisis con todos los valores en cero.")
