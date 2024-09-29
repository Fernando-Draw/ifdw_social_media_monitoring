from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from .smmonitor_model_project_task_hashtags import SmmonitorProjectTaskHashtags
from odoo.tools.translate import _
from datetime import datetime, timedelta
from pytz import timezone

class SmmonitorTaskAnalytics(models.Model):
    _name = 'smm.task.analytics.date'
    _description = """Lista de registros guardados para la tarea actual desde la cual se calculan la grán mayoría del
                      resto de valores del módulo"""
    
    # Campos principales de esta clase
    smm_datetask_id = fields.Many2one('project.task', string='Título', required=True, ondelete='cascade')
    datetakesdata = fields.Date(string='Fecha de registro', required=True, store=True)
    engagement = fields.Float(string='Vinculación % (Egagmt)', compute='_compute_smmonitor_engagement',digits=(6,2), store=True)
    reach = fields.Integer(string='Alcance', store=True)
    interactions = fields.Integer(string='Interacciones (CTR)', store=True)
    impressions = fields.Integer(string='Impresiones', store=True)

    # Campos principales del módulo Proyectos vinculados aquí
    name = fields.Char(related='smm_datetask_id.name', string='Titulo')
    stage_id = fields.Many2one(related='smm_datetask_id.stage_id', string='Etapas')
    partner_id = fields.Many2one(related='smm_datetask_id.partner_id', string='Cliente')
    company_id = fields.Many2one(related='smm_datetask_id.company_id', string='Compañia')
    parent_id = fields.Many2one(related='smm_datetask_id.parent_id', string='Proyecto')
    milestone_id = fields.Many2one(related='smm_datetask_id.milestone_id', string='Hitos')
    project_id = fields.Many2one('project.project', related='smm_datetask_id.project_id', string='Proyecto')
    user_ids = fields.Many2many('res.users', related='smm_datetask_id.user_ids', string='Asignados')
    tag_ids = fields.Many2many(related='smm_datetask_id.tag_ids', string="Etiquetas")
    depend_on_ids = fields.Many2many(related='smm_datetask_id.depend_on_ids', string='Bloqueado por')
    dependent_ids = fields.Many2many(related='smm_datetask_id.dependent_ids', string='Bloquear')
    personal_stage_type_ids = fields.Many2many(related='smm_datetask_id.personal_stage_type_ids', string='Etapas Personales')
    state = fields.Selection(related='smm_datetask_id.state', string='Estado')
    priority = fields.Selection(related='smm_datetask_id.priority', string='Prioridad')
    date_last_stage_update = fields.Datetime(related='smm_datetask_id.date_last_stage_update', string='Última actualización de etapa')
    active = fields.Boolean(related='smm_datetask_id.active', string='Activo')
    allow_milestones = fields.Boolean(related='smm_datetask_id.allow_milestones', string='Permitir hitos')
    date_assign = fields.Datetime(related='smm_datetask_id.date_assign', string='Fecha de Asignación')
    date_deadline = fields.Datetime(related='smm_datetask_id.date_deadline', string='Fecha limite')
    message_is_follower = fields.Boolean(related='smm_datetask_id.message_is_follower', string='Seguida')
    closed_subtask_count = fields.Integer(related='smm_datetask_id.closed_subtask_count', string='Numero de sub-tareas cerradas')
    subtask_count = fields.Integer(related='smm_datetask_id.subtask_count', string='Numero de sub-tareas')
    
    # Campos principales del módulo Proyectos/tareas de los campos ampliados en "SmmonitorProjectTaskHashtags" vinculados aquí.
    smm_hashtag_task_ids = fields.Many2many(related='smm_datetask_id.smm_hashtag_task_ids', string='Hashtags RR.SS.')

    # Guardamos el offset y la zona horaria en el usuario actual
    @api.model
    def save_tz_offset(self, offset, timezone):
        self.env.user.tz_offset = int(offset)
        self.env.user.tz = timezone

    # Cálculo de engagement en base al valor especificado en el campo de normalización de proyectos
    @api.depends('interactions', 'reach', 'smm_datetask_id.project_id.engagement_normalization')
    def _compute_smmonitor_engagement(self):
        for record in self:
            if record.reach and record.interactions:
                engagement_normalization_value = float(record.smm_datetask_id.project_id.engagement_normalization or 100)
                record.engagement = (record.interactions * record.reach) / engagement_normalization_value
            else:
                record.engagement = 0.0
    
    @api.depends('smm_datetask_id')
    def _compute_smmonitor_user_ids(self):
        for record in self:
            record.user_ids = record.smm_datetask_id.user_ids

    # Restricciones para los campos
    @api.constrains('datetakesdata', 'engagement', 'reach', 'interactions', 'impressions')
    def _check_values(self):
        for record in self:
            tz_offset = int(self.env.user.tz_offset or 0)  # Obtenemos el offset desde el usuario y aseguramos de convertir a entero
            today = fields.Date.context_today(record) - timedelta(minutes=tz_offset)
            
            if record.datetakesdata > today:
                raise ValidationError("La fecha no puede ser posterior al día de hoy.")
            if record.datetakesdata < today - timedelta(days=365):
                raise ValidationError("La fecha no puede ser anterior a un año desde hoy.")
            if record.engagement <= -1 or record.engagement > 999999.99:
                raise ValidationError("La vinculación debe estar entre 0% y 999999.99%.")
            if record.reach <= -1:
                raise ValidationError("El alcance no puede ser negativo.")
            if record.interactions <= -1:
                raise ValidationError("Las interacciones no pueden ser negativas.")
            if record.impressions <= -1:
                raise ValidationError("Las impresiones no pueden ser negativas.")
    
    # Resticción y comprobación para no dejar agregar más de un registro de valores por día (arreglar esta restricción para que tenga en cuenta la tarea)
    @api.constrains('datetakesdata')
    def _check_unique_per_day(self):
        for record in self:
            existing_records = self.env['smm.task.analytics.date'].search([
                ('datetakesdata', '>=', record.datetakesdata.strftime('%Y-%m-%d')),
                ('datetakesdata', '<', (record.datetakesdata + timedelta(days=1)).strftime('%Y-%m-%d')),
                ('smm_datetask_id', '=', record.smm_datetask_id.id)
            ])
            if existing_records and existing_records != record:
                raise ValidationError("""Ya existe un registro para el día seleccionado, no se permite la creación de 2 registros en el mismo día, para evitar sobresaturación de datos""")

##################################################################################################################################################

class SmmonitorTaskAnalyticsMeasure(models.Model):
    _name = 'smm.task.measure.analytics'
    _description = 'Datos analíticos de medias ponderadas de las mediciones tomadas'

    #  Campos principales de esta clase
    smm_measuretask_id = fields.Many2one('project.task', string='Título', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Secuencia', store=True)
    analytics_average_type = fields.Char(string='Tipo de Medición', store=True) 
    # Campos principales del módulo Proyectos/tareas vinculados aquí, para trabajar con ellos en las vistas personalizadas.
    name = fields.Char(related='smm_measuretask_id.name', string='Titulo')
    stage_id = fields.Many2one(related='smm_measuretask_id.stage_id', string='Etapas')
    partner_id = fields.Many2one(related='smm_measuretask_id.partner_id', string='Cliente')
    company_id = fields.Many2one(related='smm_measuretask_id.company_id', string='Compañía')
    parent_id = fields.Many2one(related='smm_measuretask_id.parent_id', string='Proyecto')
    milestone_id = fields.Many2one(related='smm_measuretask_id.milestone_id', string='Hitos')
    project_id = fields.Many2one('project.project', related='smm_measuretask_id.project_id', string='Proyecto')
    user_ids = fields.Many2many('res.users', related='smm_measuretask_id.user_ids', string="Asignados")
    tag_ids = fields.Many2many(related='smm_measuretask_id.tag_ids', string="Etiquetas")
    recurrence_id = fields.Many2one(related='smm_measuretask_id.recurrence_id')
    personal_stage_type_id = fields.Many2one(related='smm_measuretask_id.personal_stage_type_id', string='Etapa personal')
    personal_stage_type_ids = fields.Many2many(related='smm_measuretask_id.personal_stage_type_ids', string='Etapas personales')
    dependent_ids = fields.Many2many(related='smm_measuretask_id.dependent_ids', string='Bloquear')
    depend_on_ids = fields.Many2many(related='smm_measuretask_id.depend_on_ids', string='Bloqueado por')
    state = fields.Selection(related='smm_measuretask_id.state', string='Estado')
    active = fields.Boolean(related='smm_measuretask_id.active', string='Activo')
    allow_milestones = fields.Boolean(related='smm_measuretask_id.allow_milestones', string='Permitir hitos')
    allow_task_dependencies = fields.Boolean(related='smm_measuretask_id.allow_task_dependencies', string='Dependencias de tareas')
    rating_last_value = fields.Float(related='smm_measuretask_id.rating_last_value', string='Clasificación (/5)')
    rating_count = fields.Integer(related='smm_measuretask_id.rating_count', string='Recuento de clasificaciones')
    rating_avg = fields.Float(related='smm_measuretask_id.rating_avg', string='Promedio de calificación')
    rating_active = fields.Boolean(related='smm_measuretask_id.rating_active', string='Calificación de clientes')
    rating_avg_text = fields.Selection(related='smm_measuretask_id.rating_avg_text', string='Texto de calificación')
    recurring_count = fields.Integer(related='smm_measuretask_id.recurring_count', string="Tareas recurrentes")
    subtask_count = fields.Integer(related='smm_measuretask_id.subtask_count', string="Recuento de tareas")
    closed_subtask_count = fields.Integer(related='smm_measuretask_id.closed_subtask_count', string="Recuento de tareas cerradas")
    dependent_tasks_count = fields.Integer(related='smm_measuretask_id.dependent_tasks_count', string="Tareas dependientes")
    priority = fields.Selection(related='smm_measuretask_id.priority', string='Prioridad')
    message_is_follower = fields.Boolean(related='smm_measuretask_id.message_is_follower', string='Seguida')
    date_assign = fields.Datetime(related='smm_measuretask_id.date_assign', string='Fecha de Asignación')
    is_project_map_empty = fields.Boolean(related='smm_measuretask_id.is_project_map_empty', string="¿El mapa del proyecto está sin tareas?")
    has_multi_sol = fields.Boolean(related='smm_measuretask_id.has_multi_sol')
    date_last_stage_update = fields.Datetime(related='smm_measuretask_id.date_last_stage_update', string='Última actualización de etapa')

    # Campos principales del módulo Proyectos/tareas de los campos ampliados en "SmmonitorProjectTask" vinculados aquí.
    datetakesdata = fields.Date(related='smm_measuretask_id.datetakesdata', string='Fecha de registro', store=True)

    # Campos principales del módulo Proyectos/tareas de los campos ampliados en "SmmonitorProjectTaskHashtags" vinculados aquí.
    smm_hashtag_task_ids = fields.Many2many(related='smm_measuretask_id.smm_hashtag_task_ids', string='Hashtags RR.SS.')

    # Ordena por fecha lista de registros indicando cual es el primer registro y el último registro. 
    # Además si no hay registros, los deja en valor "0" o "False".
    @api.depends('smm_measuretask_id.smm_date_task_ids.datetakesdata',
                 'smm_measuretask_id.smm_date_task_ids.engagement',
                 'smm_measuretask_id.smm_date_task_ids.interactions',
                 'smm_measuretask_id.smm_date_task_ids.reach',
                 'smm_measuretask_id.smm_date_task_ids.impressions')
    def _compute_first_and_last_data(self):
        for task in self:
            sorted_records_date = task.smm_measuretask_id.smm_date_task_ids.sorted(key=lambda r: r.datetakesdata)
            if sorted_records_date:
                first_record = sorted_records_date[0]
                last_record = sorted_records_date[-1]

                task.firstdata_datetakesdata = first_record.datetakesdata
                task.firstdata_engagement = first_record.engagement
                task.firstdata_interactions = first_record.interactions
                task.firstdata_reach = first_record.reach
                task.firstdata_impressions = first_record.impressions

                task.latestdata_datetakesdata = last_record.datetakesdata
                task.latestdata_engagement = last_record.engagement
                task.latestdata_interactions = last_record.interactions
                task.latestdata_reach = last_record.reach
                task.latestdata_impressions = last_record.impressions
            else:
                # Si no hay registros, establecemos todos los valores a False o 0
                task.firstdata_datetakesdata = task.latestdata_datetakesdata = False
                task.firstdata_engagement = task.latestdata_engagement = 0
                task.firstdata_interactions = task.latestdata_interactions = 0
                task.firstdata_reach = task.latestdata_reach = 0
                task.firstdata_impressions = task.latestdata_impressions = 0
    
    # Campos para medias ponderadas y tasas de crecimiento del módulo IfDw Social Media Monitoring.
    firstdata_datetakesdata = fields.Date(compute='_compute_first_and_last_data', string='Registro inicial Fecha', store=True)
    latestdata_datetakesdata = fields.Date(compute='_compute_first_and_last_data', string='Registro final Fecha', store=True)

    firstdata_engagement = fields.Float(compute='_compute_first_and_last_data', string='Registro inicial Vinculación', store=True)
    taverage01_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 1 Vinculación', store=True)
    taverage02_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 2 Vinculación', store=True)
    taverage03_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 3 Vinculación', store=True)
    taverage04_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 4 Vinculación', store=True)
    taverage05_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 5 Vinculación', store=True)
    taverage06_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 6 Vinculación', store=True)
    taverage07_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 7 Vinculación', store=True)
    taverage08_engagement = fields.Float(compute='_compute_averages', string='Cálculo media 8 Vinculación', store=True)
    latestdata_engagement = fields.Float(compute='_compute_first_and_last_data', string='Registro final Vinculación', store=True)

    firstdata_interactions = fields.Integer(compute='_compute_first_and_last_data', string='Registro inicial Interacciones', store=True)
    taverage01_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 1 Interacciones', store=True)
    taverage02_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 2 Interacciones', store=True)
    taverage03_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 3 Interacciones', store=True)
    taverage04_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 4 Interacciones', store=True)
    taverage05_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 5 Interacciones', store=True)
    taverage06_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 6 Interacciones', store=True)
    taverage07_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 7 Interacciones', store=True)
    taverage08_interactions = fields.Integer(compute='_compute_averages', string='Cálculo media 8 Interacciones', store=True)
    latestdata_interactions = fields.Integer(compute='_compute_first_and_last_data', string='Registro final Interacciones', store=True)

    firstdata_reach = fields.Integer(compute='_compute_first_and_last_data', string='Registro inicial Alcance', store=True)
    taverage01_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 1 Alcance', store=True)
    taverage02_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 2 Alcance', store=True)
    taverage03_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 3 Alcance', store=True)
    taverage04_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 4 Alcance', store=True)
    taverage05_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 5 Alcance', store=True)
    taverage06_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 6 Alcance', store=True)
    taverage07_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 7 Alcance', store=True)
    taverage08_reach = fields.Integer(compute='_compute_averages', string='Cálculo media 8 Alcance', store=True)
    latestdata_reach = fields.Integer(compute='_compute_first_and_last_data', string='Registro final Alcance', store=True)

    firstdata_impressions = fields.Integer(compute='_compute_first_and_last_data', string='Registro inicial Impresiones', store=True)
    taverage01_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 1 Impresiones', store=True)
    taverage02_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 2 Impresiones', store=True)
    taverage03_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 3 Impresiones', store=True)
    taverage04_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 4 Impresiones', store=True)
    taverage05_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 5 Impresiones', store=True)
    taverage06_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 6 Impresiones', store=True)
    taverage07_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 7 Impresiones', store=True)
    taverage08_impressions = fields.Integer(compute='_compute_averages', string='Cálculo media 8 Impresiones', store=True)
    latestdata_impressions = fields.Integer(compute='_compute_first_and_last_data', string='Registro final Impresiones', store=True)
    
    growthrate_engagement = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>F Vinculación', store=True)
    growthrate_engagement_start_to_first = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>1 Vinculación', store=True)
    growthrate_engagement_1_to_2 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 1>2 Vinculación', store=True)
    growthrate_engagement_2_to_3 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 2>3 Vinculación', store=True)
    growthrate_engagement_3_to_4 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 3>4 Vinculación', store=True)
    growthrate_engagement_4_to_5 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 4>5 Vinculación', store=True)
    growthrate_engagement_5_to_6 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 5>6 Vinculación', store=True)
    growthrate_engagement_6_to_7 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 6>7 Vinculación', store=True)
    growthrate_engagement_7_to_8 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 7>8 Vinculación', store=True)
    growthrate_engagement_last_to_end = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 8>F Vinculación', store=True)

    growthrate_interactions = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>F Interacciones', store=True)
    growthrate_interactions_start_to_first = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>1 Interacciones', store=True)
    growthrate_interactions_1_to_2 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 1>2 Interacciones', store=True)
    growthrate_interactions_2_to_3 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 2>3 Interacciones', store=True)
    growthrate_interactions_3_to_4 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 3>4 Interacciones', store=True)
    growthrate_interactions_4_to_5 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 4>5 Interacciones', store=True)
    growthrate_interactions_5_to_6 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 5>6 Interacciones', store=True)
    growthrate_interactions_6_to_7 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 6>7 Interacciones', store=True)
    growthrate_interactions_7_to_8 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 7>8 Interacciones', store=True)
    growthrate_interactions_last_to_end = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 8>F Interacciones', store=True)

    growthrate_reach = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>F Alcance', store=True)
    growthrate_reach_start_to_first = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>1 Alcance', store=True)
    growthrate_reach_1_to_2 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 1>2 Alcance', store=True)
    growthrate_reach_2_to_3 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 2>3 Alcance', store=True)
    growthrate_reach_3_to_4 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 3>4 Alcance', store=True)
    growthrate_reach_4_to_5 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 4>5 Alcance', store=True)
    growthrate_reach_5_to_6 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 5>6 Alcance', store=True)
    growthrate_reach_6_to_7 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 6>7 Alcance', store=True)
    growthrate_reach_7_to_8 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 7>8 Alcance', store=True)
    growthrate_reach_last_to_end = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 8>F Alcance', store=True)

    growthrate_impressions = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>F Impresiones', store=True)
    growthrate_impressions_start_to_first = fields.Float(compute='_compute_averages', string='Tasa Crecimiento I>1 Impresiones', store=True)
    growthrate_impressions_1_to_2 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 1>2 Impresiones', store=True)
    growthrate_impressions_2_to_3 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 2>3 Impresiones', store=True)
    growthrate_impressions_3_to_4 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 3>4 Impresiones', store=True)
    growthrate_impressions_4_to_5 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 4>5 Impresiones', store=True)
    growthrate_impressions_5_to_6 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 5>6 Impresiones', store=True)
    growthrate_impressions_6_to_7 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 6>7 Impresiones', store=True)
    growthrate_impressions_7_to_8 = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 7>8 Impresiones', store=True)
    growthrate_impressions_last_to_end = fields.Float(compute='_compute_averages', string='Tasa Crecimiento 8>F Impresiones', store=True)

    # Asignación de secuencia numérica a los campos de medias ponderadas y tasas de crecimiento para cada variable repartidas 
    # # en 19 valores.
    def assign_sequence_to_fields(data):
        sequence_start = 0
        for variable in ['engagement', 'interactions', 'reach', 'impressions']:
            # Asignar secuencia a firstdata, taverage y latestdata
            data[f'firstdata_{variable}']['sequence'] = sequence_start
            for i in range(1, 9):
                data[f'taverage0{i}_{variable}']['sequence'] = sequence_start + (i * 2)
            data[f'latestdata_{variable}']['sequence'] = sequence_start + 18  # Último valor

            # Asignar secuencia para las tasas de crecimiento intercaladas
            data[f'growthrate_{variable}_start_to_first']['sequence'] = sequence_start + 1
            for i in range(1, 8):
                data[f'growthrate_{variable}_{i}_to_{i+1}']['sequence'] = sequence_start + (i * 2) + 1
            data[f'growthrate_{variable}_last_to_end']['sequence'] = sequence_start + 17

        return data

    # Cálculo de campos computados para las 8 medias respecto del tiempo comprendido entre la fecha del primer juego de 
    # datos y la fecha del ultimo juego de datos introducidos.
    @api.depends('smm_measuretask_id.smm_date_task_ids.datetakesdata',
             'smm_measuretask_id.smm_date_task_ids.engagement',
             'smm_measuretask_id.smm_date_task_ids.interactions',
             'smm_measuretask_id.smm_date_task_ids.reach',
             'smm_measuretask_id.smm_date_task_ids.impressions',
             'firstdata_datetakesdata', 'firstdata_engagement', 
             'firstdata_interactions', 'firstdata_reach', 
             'firstdata_impressions','latestdata_datetakesdata', 
             'latestdata_engagement', 'latestdata_interactions', 
             'latestdata_reach', 'latestdata_impressions')
    def _compute_averages(self):
        for task in self:
            metricsanalyze = ['engagement', 'reach', 'interactions', 'impressions']
            for metric in metricsanalyze:
                setattr(task, f'growthrate_{metric}', None)
                setattr(task, f'growthrate_{metric}_start_to_first', None)
                setattr(task, f'growthrate_{metric}_last_to_end', None)
                for i in range(1, 9):
                    setattr(task, f'taverage0{i}_{metric}', None)
                    if i <= 7:
                        setattr(task, f'growthrate_{metric}_{i}_to_{i+1}', None)

            if task.firstdata_datetakesdata and task.latestdata_datetakesdata:
                start_date = task.firstdata_datetakesdata
                end_date = task.latestdata_datetakesdata
                total_days = (end_date - start_date).days
                if total_days > 0:
                    interval = total_days / 9
                    all_records = task.smm_measuretask_id.sorted(key=lambda r: r.datetakesdata)

                    for i in range(1, 9):
                        target_date = start_date + timedelta(days=interval * i)

                        before = next((r for r in reversed(all_records) if r.datetakesdata <= target_date), None)
                        after = next((r for r in all_records if r.datetakesdata >= target_date), None)

                        if before and after:
                            # Interpolar valores
                            days_before = (target_date - before.datetakesdata).days
                            days_after = (after.datetakesdata - target_date).days
                            total_days = days_before + days_after
                            weight_before = 1 - (days_before / total_days) if total_days > 0 else 0.5
                            weight_after = 1 - weight_before

                            engagement = (before.engagement * weight_before) + (after.engagement * weight_after)
                            interactions = int((before.interactions * weight_before) + (after.interactions * weight_after))
                            reach = int((before.reach * weight_before) + (after.reach * weight_after))
                            impressions = int((before.impressions * weight_before) + (after.impressions * weight_after))
                        elif before:
                            engagement, interactions, reach, impressions = before.engagement, before.interactions, before.reach, before.impressions
                        elif after:
                            engagement, interactions, reach, impressions = after.engagement, after.interactions, after.reach, after.impressions
                        else:
                            engagement, interactions, reach, impressions = None, None, None, None

                        setattr(task, f'taverage0{i}_engagement', engagement)
                        setattr(task, f'taverage0{i}_interactions', interactions)
                        setattr(task, f'taverage0{i}_reach', reach)
                        setattr(task, f'taverage0{i}_impressions', impressions)

                    # # Calcular tasas de crecimiento entre inicio a fin
                    # for metric in metricsanalyze:
                    #     start_value = getattr(task, f'firstdata_{metric}')
                    #     end_value = getattr(task, f'latestdata_{metric}')
                    #     growthrate = self._calculate_growthrate(start_value, end_value) if start_value is not None and end_value is not None else 0
                    #     setattr(task, f'growthrate_{metric}', growthrate)

                    # Calcular tasas de crecimiento entre inicio a fin
                    for metric in metricsanalyze:
                        growthrate_total = (
                            self._calculate_growthrate(
                                getattr(task, f'firstdata_{metric}'), getattr(task, f'latestdata_{metric}')
                            )
                            if getattr(task, f'firstdata_{metric}') is not None
                            and getattr(task, f'latestdata_{metric}') is not None
                            else 0
                        )
                        setattr(task, f'growthrate_{metric}', growthrate_total)

                    # # Calcular tasas de crecimiento entre medias
                    # for i in range(1, 8):
                    #     for metric in metricsanalyze:
                    #         start_value = getattr(task, f'taverage0{i}_{metric}')
                    #         end_value = getattr(task, f'taverage0{i+1}_{metric}')
                    #         growthrate = self._calculate_growthrate(start_value, end_value) if start_value is not None and end_value is not None else 0
                    #         setattr(task, f'growthrate_{metric}_{i}_to_{i+1}', growthrate)

                    # Calcular tasas de crecimiento entre medias
                    for i in range(1, 8):
                        for metric in metricsanalyze:
                            growthrate_range = (
                                self._calculate_growthrate(
                                    getattr(task, f'taverage0{i}_{metric}'), getattr(task, f'taverage0{i+1}_{metric}')
                                )
                                if getattr(task, f'taverage0{i}_{metric}') is not None
                                and getattr(task, f'taverage0{i+1}_{metric}') is not None
                                else 0
                            )
                            setattr(task, f'growthrate_{metric}_{i}_to_{i+1}', growthrate_range)

                    # Calcular tasa de crecimiento entre valor inicial y primera media, y entre última media y valor final
                    for metric in metricsanalyze:
                        start_to_first = (
                            self._calculate_growthrate(
                                getattr(task, f'firstdata_{metric}'), getattr(task, f'taverage01_{metric}')
                            )
                            if getattr(task, f'firstdata_{metric}') is not None
                            and getattr(task, f'taverage01_{metric}') is not None
                            else 0
                        )
                        last_to_end = (
                            self._calculate_growthrate(
                                getattr(task, f'taverage08_{metric}'), getattr(task, f'latestdata_{metric}')
                            )
                            if getattr(task, f'taverage08_{metric}') is not None
                            and getattr(task, f'latestdata_{metric}') is not None
                            else 0
                        )
                        setattr(task, f'growthrate_{metric}_start_to_first', start_to_first)
                        setattr(task, f'growthrate_{metric}_last_to_end', last_to_end)
            else:
                # Asegurarse de asignar valores por defecto si falta algún dato inicial
                task.growthrate_engagement = 0
                task.growthrate_interactions = 0
                task.growthrate_reach = 0
                task.growthrate_impressions = 0
                for metric in metricsanalyze:
                    setattr(task, f'growthrate_{metric}_start_to_first', 0)
                    setattr(task, f'growthrate_{metric}_last_to_end', 0)
                for metric in metricsanalyze:
                    for i in range(1, 8):
                        setattr(task, f'growthrate_{metric}_{i}_to_{i+1}', 0)

    @api.model
    def _calculate_growthrate(self, start_value, end_value):
        if start_value == 0:
            return 100 if end_value > 0 else 0
        return ((end_value - start_value) / start_value) * 100
    
    # Tiene pinta de que este trozo de código ya no es necesario, ya que en su momento calculaba las medidas finales
    # @api.depends('smm_measuretask_id', 
    #              'smm_measuretask_id.datetakesdata', 
    #              'smm_measuretask_id.engagement', 
    #              'smm_measuretask_id.interactions', 
    #              'smm_measuretask_id.reach', 
    #              'smm_measuretask_id.impressions')
    # def _compute_latest_analytics(self):
    #     for task in self:
    #         latest_record = task.smm_measuretask_id.sorted('datetakesdata', reverse=True)[:1]
    #         task.latestdatetakesdata = latest_record.datetakesdata if latest_record else False
    #         task.latestengagement = latest_record.engagement if latest_record else 0.0
    #         task.latestinteractions = latest_record.interactions if latest_record else 0
    #         task.latestreach = latest_record.reach if latest_record else 0
    #         task.latestimpressions = latest_record.impressions if latest_record else 0

    @api.depends(
        'firstdata_engagement', 'taverage01_engagement', 'taverage02_engagement',
        'taverage03_engagement', 'taverage04_engagement', 'taverage05_engagement',
        'taverage06_engagement', 'taverage07_engagement', 'taverage08_engagement',
        'latestdata_engagement', 'firstdata_interactions', 'taverage01_interactions',
        'taverage02_interactions', 'taverage03_interactions', 'taverage04_interactions',
        'taverage05_interactions', 'taverage06_interactions', 'taverage07_interactions',
        'taverage08_interactions', 'latestdata_interactions', 'firstdata_reach',
        'taverage01_reach', 'taverage02_reach', 'taverage03_reach', 'taverage04_reach',
        'taverage05_reach', 'taverage06_reach', 'taverage07_reach', 'taverage08_reach',
        'latestdata_reach', 'firstdata_impressions', 'taverage01_impressions',
        'taverage02_impressions', 'taverage03_impressions', 'taverage04_impressions',
        'taverage05_impressions', 'taverage06_impressions', 'taverage07_impressions',
        'taverage08_impressions', 'latestdata_impressions'
    )
    def _update_analytics_average_type(self):
        field_to_type = {
            'engagement': [
                'firstdata_engagement', 'taverage01_engagement', 'taverage02_engagement',
                'taverage03_engagement', 'taverage04_engagement', 'taverage05_engagement',
                'taverage06_engagement', 'taverage07_engagement', 'taverage08_engagement',
                'latestdata_engagement', 'growthrate_engagement', 'growthrate_engagement_start_to_first',
                'growthrate_engagement_1_to_2', 'growthrate_engagement_2_to_3', 'growthrate_engagement_3_to_4',
                'growthrate_engagement_4_to_5', 'growthrate_engagement_5_to_6', 'growthrate_engagement_6_to_7',
                'growthrate_engagement_7_to_8', 'growthrate_engagement_last_to_end'
            ],
            'interactions': [
                'firstdata_interactions', 'taverage01_interactions', 'taverage02_interactions',
                'taverage03_interactions', 'taverage04_interactions', 'taverage05_interactions',
                'taverage06_interactions', 'taverage07_interactions', 'taverage08_interactions',
                'latestdata_interactions', 'growthrate_interactions', 'growthrate_interactions_start_to_first',
                'growthrate_interactions_1_to_2', 'growthrate_interactions_2_to_3', 'growthrate_interactions_3_to_4',
                'growthrate_interactions_4_to_5', 'growthrate_interactions_5_to_6', 'growthrate_interactions_6_to_7',
                'growthrate_interactions_7_to_8', 'growthrate_interactions_last_to_end'
            ],
            'reach': [
                'firstdata_reach', 'taverage01_reach', 'taverage02_reach',
                'taverage03_reach', 'taverage04_reach', 'taverage05_reach',
                'taverage06_reach', 'taverage07_reach', 'taverage08_reach',
                'latestdata_reach', 'growthrate_reach', 'growthrate_reach_start_to_first',
                'growthrate_reach_1_to_2', 'growthrate_reach_2_to_3', 'growthrate_reach_3_to_4',
                'growthrate_reach_4_to_5', 'growthrate_reach_5_to_6', 'growthrate_reach_6_to_7',
                'growthrate_reach_7_to_8', 'growthrate_reach_last_to_end'
            ],
            'impressions': [
                'firstdata_impressions', 'taverage01_impressions', 'taverage02_impressions',
                'taverage03_impressions', 'taverage04_impressions', 'taverage05_impressions',
                'taverage06_impressions', 'taverage07_impressions', 'taverage08_impressions',
                'latestdata_impressions', 'growthrate_impressions', 'growthrate_impressions_start_to_first',
                'growthrate_impressions_1_to_2', 'growthrate_impressions_2_to_3', 'growthrate_impressions_3_to_4',
                'growthrate_impressions_4_to_5', 'growthrate_impressions_5_to_6', 'growthrate_impressions_6_to_7',
                'growthrate_impressions_7_to_8', 'growthrate_impressions_last_to_end'
            ]
        }

        for record in self:
            for field_type, fields in field_to_type.items():
                for field in fields:
                    if record[field]:
                        record.analytics_average_type = field_type
                        break  # Salir del bucle interno si se encuentra una coincidencia
                if record.analytics_average_type:
                    break  # Salir del bucle externo si ya se ha establecido el tipo

##################################################################################################################################################

class SmmonitorProjectTask(models.Model):
    _inherit = 'project.task'
    _description = 'Tareas de proyectos, personalización para S.M. Monitor'

    # Campos principales de esta clase
    smm_date_task_ids = fields.One2many('smm.task.analytics.date', 'smm_datetask_id', string='Datos analíticos')
    smm_measure_task_ids = fields.One2many('smm.task.measure.analytics', 'smm_measuretask_id', string='Medias y Tasas')
    smm_hashtag_task_ids = fields.Many2many('smm.task.hashtags', string='Hashtags RR.SS.')
    post_type = fields.Selection([('image', 'Imágen'), ('carrusel', 'Carrusel'), ('short video', 'Video Corto'),
                                  ('long video', 'Video Largo'), ('history 24h', 'Historía 24h')], string='Tipo de publicación', default='history 24h')
    ab_test = fields.Selection([('no', 'No'), ('yes', 'Sí')], string='Prueba A/B', default='no')
    temp_datetakesdata = fields.Date(string='Fecha de registro', default=fields.Date.context_today)
    temp_interactions = fields.Integer(string='Interacciones (CTR)', default=0)
    temp_reach = fields.Integer(string='Alcance', default=0)
    temp_impressions = fields.Integer(string='Impresiones', default=0)
    analytics_count = fields.Integer(compute='_compute_analytics_count', string='Número de registros')
    can_add_analytics = fields.Boolean(compute='_compute_can_add_analytics')
    
    # Campos principales del módulo de los campos ampliados en "SmmonitorTaskAnalytics" vinculados aquí.
    datetakesdata = fields.Date(related='smm_date_task_ids.datetakesdata', string='Fecha de registro', store=True)
    engagement = fields.Float(related='smm_date_task_ids.engagement', string='Vinculación % (Egagmt)', store=True)
    reach = fields.Integer(related='smm_date_task_ids.reach', string='Alcance', store=True)
    interactions = fields.Integer(related='smm_date_task_ids.interactions', string='Interacciones (CTR)', store=True)
    impressions = fields.Integer(related='smm_date_task_ids.impressions', string='Impresiones', store=True)

    # Campos principales del módulo de los campos ampliados en "SmmonitorTaskAnalyticsMeasure" vinculados aquí.
    firstdata_datetakesdata = fields.Date(related='smm_measure_task_ids.firstdata_datetakesdata', string='Registro inicial Fecha', store=True)
    latestdata_datetakesdata = fields.Date(related='smm_measure_task_ids.latestdata_datetakesdata', string='Registro final Fecha', store=True)

    growthrate_engagement = fields.Float(related='smm_measure_task_ids.growthrate_engagement', string='Tasa Crecimiento I>F Vinculación', store=True)
    growthrate_interactions = fields.Float(related='smm_measure_task_ids.growthrate_interactions', string='Tasa Crecimiento I>F Interacciones', store=True)
    growthrate_reach = fields.Float(related='smm_measure_task_ids.growthrate_reach', string='Tasa Crecimiento I>F Alcance', store=True)
    growthrate_impressions = fields.Float(related='smm_measure_task_ids.growthrate_impressions', string='Tasa Crecimiento I>F Impresiones', store=True)

    # Campos principales del módulo de los campos ampliados en "SmmonitorTaskAnalyticsMeasure" vinculados aquí.
    # hashtags_ids = fields.Many2many('smm.task.hashtags', string='Hashtags RR.SS.')

    # Guardamos el offset y la zona horaria en el usuario actual.
    def save_tz_offset(self, offset, timezone):
        self.env.user.tz_offset = int(offset)
        self.env.user.tz = timezone

    # Método para generar hashtags en el formato adecuado y copiarlos al portapeles.
    def action_copy_hashtags(self):
        self.ensure_one()
        hashtags = [f'#{tag.name}' for tag in self.smm_hashtag_task_ids]
        hashtag_text = '\n'.join(hashtags)

        if not hashtag_text:
            raise UserError(_("No hay hashtags asociados a esta tarea/publicación."))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hashtags copiados'),
                'message': _('Los hashtags han sido copiados al portapapeles.'),
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'smmonitor_copy_hashtags',
                    'params': {
                        'content': hashtag_text
                    }
                }
            }
        }
    
    # Llama a JS que calcula el offset de tiempo que puede existir entre un usuario registrado y la hora del servidor
    # y si no es correcto lanza error.
    @api.model
    def get_user_tz_offset(self):
        self.ensure_one()
        try:
            tz_offset = int(self.env.user.tz_offset) # Asegurarse de que sea un entero
            return tz_offset
        except (ValueError, TypeError) as e:
            _logger.error(f"Error al obtener el offset de la zona horaria: {e}")
            return 0 # Valor predeterminado si hay algún problema

    # Calcula el nº de registros analíticos que existen
    @api.depends('smm_date_task_ids')
    def _compute_analytics_count(self):
        self.ensure_one()
        for task in self:
            task.analytics_count = len(task.smm_date_task_ids)

    # Restricciones para campos temporales de pestaña "Control RR.SS."
    @api.depends('temp_interactions', 'temp_reach', 'temp_impressions')
    def _compute_can_add_analytics(self):
        self.ensure_one()
        for task in self:
            task.can_add_analytics = any([
                task.temp_interactions >= 0,
                task.temp_reach >= 0,
                task.temp_impressions >= 0
            ])

    # Restricciones para campos temporales de pestaña "Control RR.SS."
    @api.constrains('temp_datetakesdata', 'temp_interactions', 'temp_reach', 'temp_impressions')
    def _check_temp_values(self):
        self.ensure_one()
        for task in self:
            tz_offset = int(self.env.user.tz_offset or 0)  # Obtenemos el offset desde el usuario y aseguramos de convertir a entero
            today = fields.Date.context_today(task) - timedelta(minutes=tz_offset)

            if task.temp_datetakesdata > today:
                raise ValidationError("La fecha no puede ser posterior al día de hoy.")
            if task.temp_datetakesdata < today - timedelta(days=365):
                raise ValidationError("La fecha no puede ser anterior a un año desde hoy.")
            if task.temp_interactions <= -1:
                raise ValidationError("Las interacciones no pueden ser negativas.")
            if task.temp_reach <= -1:
                raise ValidationError("El alcance no puede ser negativo.")
            if task.temp_impressions <= -1:
                raise ValidationError("Las impresiones no pueden ser negativas.")

    # Acción para añadir los valores de registro a la tabla de datos para registrar de las 4 variables de cada tarea
    def action_add_analytics(self):
        self.ensure_one()
        # Validación para valores negativos y decimales.
        if self.temp_interactions < 0 or self.temp_reach < 0 or self.temp_impressions < 0:
            raise ValidationError("No pueden ser valores negativos.")
        if (self.temp_interactions % 1) != 0 or (self.temp_reach % 1) != 0 or (self.temp_impressions % 1) != 0:
            raise ValidationError("Deben ser números enteros (sin decimales).")
        # Crear el registro de análisis.
        if self.can_add_analytics:
            self.env['smm.task.analytics.date'].create({
            'smm_datetask_id': self.id,
            'datetakesdata': self.temp_datetakesdata,
            'interactions': self.temp_interactions,
            'reach': self.temp_reach,
            'impressions': self.temp_impressions,
        })

        # Resetear los valores temporales.
        self.write({
            'temp_datetakesdata': fields.Date.context_today(self),
            'temp_interactions': 0,
            'temp_reach': 0,
            'temp_impressions': 0,
        })
        # Actualizar los campos de la clase "smm.task.measure.analytics"
        update_measure_analytics_id = self.env['smm.task.measure.analytics'].search([('smm_measuretask_id', '=', self.id)])
        if update_measure_analytics_id:
            update_measure_analytics_id._compute_first_and_last_data()
            update_measure_analytics_id._compute_averages()
        else:
            # Si no existe, crear un nuevo registro
            self.env['smm.task.measure.analytics'].create({
                'smm_measuretask_id': self.id,
            })

##################################################################################################################################################

class SmmonitorProject(models.Model):
    _inherit = 'project.project'

    # Campo principal de esta clase
    engagement_normalization = fields.Selection(
        selection=[('100', '100'), ('1000', '1000'), ('10000', '10000')],
        string='Normalización de Vinculación',
        default='100',
        help="Selecciona el valor adecuado para ajustar y normalizar el cálculo de la Vinculación (Engagement), en base a la cantidad de seguidores que existan en la red social que vas a gestionar con este proyecto."
    )