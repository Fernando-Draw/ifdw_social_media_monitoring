from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request
from datetime import datetime, timedelta
from pytz import timezone, utc

class SmmonitorTaskAnalytics(models.Model):
    _name = 'project.task.smmonitor'
    _description = 'Lista de registros guardados para la tarea actual desde la cual se calculan la grán mayoría del resto de valores del módulo'
    
    # Campos principales del módulo IfDw Social Media Monitoring
    smmonitor_task_id = fields.Many2one('project.task', string='Titulo', required=True, ondelete='cascade')
    datetakesdata = fields.Date(string='Fecha de registro', required=True)  # Quitamos default aquí.
    engagement = fields.Float(string='Vinculación % (Egagmt)', compute='_compute_smmonitor_engagement',digits=(6,2), store=True)
    interactions = fields.Integer(string='Interacciones (CTR)', store=True)
    reach = fields.Integer(string='Alcance', store=True)
    impressions = fields.Integer(string='Impresiones', store=True)
    # Campos principales del módulo Proyectos vinculados aquí, para trabajar con ellos en las vistas personalizadas
    name = fields.Char(related='smmonitor_task_id.name', string='Titulo', store=True)
    message_is_follower = fields.Boolean(related='smmonitor_task_id.message_is_follower', string='Seguida', store=True)
    stage_id = fields.Many2one(related='smmonitor_task_id.stage_id', string='Etapas', store=True)
    milestone_id = fields.Many2one(related='smmonitor_task_id.milestone_id', string='Hitos', store=True)
    partner_id = fields.Many2one(related='smmonitor_task_id.partner_id', string='Cliente', store=True)
    state = fields.Selection(related='smmonitor_task_id.state', string='Estado', store=True)
    priority = fields.Selection(related='smmonitor_task_id.priority', string='Prioridad', store=True)
    date_last_stage_update = fields.Datetime(related='smmonitor_task_id.date_last_stage_update', string='Última actualización de etapa', store=True)
    active = fields.Boolean(related='smmonitor_task_id.active', string='Activo', store=True)
    company_id = fields.Many2one(related='smmonitor_task_id.company_id', string='Compañia', store=True)
    date_assign = fields.Datetime(related='smmonitor_task_id.date_assign', string='Fecha de Asignación', store=True)
    # Campos principales del módulo Proyectos vinculados aquí, para trabajar con ellos en las vistas personalizadas
    # Campos de acceso especial para poder trabajar con ellos dadas sus caracteristicas
    user_ids = fields.Many2many('res.users', compute='_compute_smmonitor_user_ids', string="Asignados", store=True)

    @api.model
    def save_tz_offset(self, offset, timezone):
        # Guardamos el offset y la zona horaria en el usuario actual
        self.env.user.tz_offset = int(offset)
        self.env.user.tz = timezone

    @api.depends('interactions', 'reach', 'smmonitor_task_id.project_id.engagement_normalization')
    def _compute_smmonitor_engagement(self):
        for record in self:
            if record.reach and record.interactions:
                # Accedemos al project_id a través de smmonitor_task_id.project_id sin tener que crear el campo projet_id
                project = record.smmonitor_task_id.project_id
                if project:
                    engagement_normalization_value = float(project.engagement_normalization or 100)
                    record.engagement = (record.interactions * record.reach) / engagement_normalization_value
                else:
                    record.engagement = 0.0
            else:
                record.engagement = 0.0

    @api.depends('smmonitor_task_id')
    def _compute_smmonitor_user_ids(self):
        for record in self:
            record.user_ids = record.smmonitor_task_id.user_ids

    @api.constrains('datetakesdata', 'engagement', 'reach', 'interactions', 'impressions')
    def _check_values(self):
        for record in self:
            tz_offset = int(self.env.user.tz_offset or 0)  # Obtenemos el offset desde el usuario y aseguramos de convertir a entero
            today = fields.Date.context_today(record) - timedelta(minutes=tz_offset)
            
            if record.datetakesdata > today:
                raise ValidationError("La fecha no puede ser posterior al día de hoy.")
            if record.datetakesdata < today - timedelta(days=365):
                raise ValidationError("La fecha no puede ser anterior a un año desde hoy.")
            if record.engagement < 0 or record.engagement > 999999.99:
                raise ValidationError("La vinculación debe estar entre 0% y 999999.99%.")
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
    _description = 'Tareas de proyectos, personalización para S.M. Monitor'

    def save_tz_offset(self, offset, timezone):
        # Guardamos el offset y la zona horaria en el usuario actual
        self.env.user.tz_offset = int(offset)
        self.env.user.tz = timezone

    smmonitor_tabs = fields.One2many('project.task.smmonitor', 'smmonitor_task_id', string='Titulo/Publicación')
    temp_datetakesdata = fields.Date(string='Fecha de registro', default=fields.Date.context_today)
    temp_engagement = fields.Float(string='Vinculación % (Egagmt)', digits=(6,2), default=0)
    temp_interactions = fields.Integer(string='Interacciones (CTR)', default=0)
    temp_reach = fields.Integer(string='Alcance', default=0)
    temp_impressions = fields.Integer(string='Impresiones', default=0)
    analytics_count = fields.Integer(compute='_compute_analytics_count', string='Número de registros')
    can_add_analytics = fields.Boolean(compute='_compute_can_add_analytics')

    # Campos computados para el primer y último registro.
    firstdata_datetakesdata = fields.Date(compute='_compute_first_and_last_data', store=True, string='Registro inicial Fecha')
    firstdata_engagement = fields.Float(compute='_compute_first_and_last_data', store=True, string='Registro inicial Vinculación')
    firstdata_interactions = fields.Integer(compute='_compute_first_and_last_data', store=True, string='Registro inicial Interacciones')
    firstdata_reach = fields.Integer(compute='_compute_first_and_last_data', store=True, string='Registro inicial Alcance')
    firstdata_impressions = fields.Integer(compute='_compute_first_and_last_data', store=True, string='Registro inicial Impresiones')

    latestdata_datetakesdata = fields.Date(compute='_compute_first_and_last_data', store=True, string='Registro final Fecha')
    latestdata_engagement = fields.Float(compute='_compute_first_and_last_data', store=True, string='Registro final Vinculación')
    latestdata_interactions = fields.Integer(compute='_compute_first_and_last_data', store=True, string='Registro final Interacciones')
    latestdata_reach = fields.Integer(compute='_compute_first_and_last_data', store=True, string='Registro final Alcance')
    latestdata_impressions = fields.Integer(compute='_compute_first_and_last_data', store=True, string='Registro final Impresiones')

    # Ordena por fecha lista de registros indicando cual es el primer registro y el último registro. Además si no hay registros, los deja en valor "0" o "False"
    @api.depends('smmonitor_tabs.datetakesdata', 'smmonitor_tabs.engagement', 'smmonitor_tabs.reach', 'smmonitor_tabs.interactions', 'smmonitor_tabs.impressions')
    def _compute_first_and_last_data(self):
        for task in self:
            sorted_tabs = task.smmonitor_tabs.sorted(key=lambda r: r.datetakesdata)
            if sorted_tabs:
                first_record = sorted_tabs[0]
                last_record = sorted_tabs[-1]
                
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

    # Campos para las 8 medias que se calculan comprendidas a espacios iguales (11.11111%) entre la fecha del registo inicial y final
    taverage01_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 1 Vinculación')
    taverage02_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 2 Vinculación')
    taverage03_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 3 Vinculación')
    taverage04_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 4 Vinculación')
    taverage05_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 5 Vinculación')
    taverage06_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 6 Vinculación')
    taverage07_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 7 Vinculación')
    taverage08_engagement = fields.Float(compute='_compute_averages', store=True, string='Cálculo media 8 Vinculación')

    taverage01_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 1 Interacciones')
    taverage02_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 2 Interacciones')
    taverage03_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 3 Interacciones')
    taverage04_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 4 Interacciones')
    taverage05_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 5 Interacciones')
    taverage06_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 6 Interacciones')
    taverage07_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 7 Interacciones')
    taverage08_interactions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 8 Interacciones')

    taverage01_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 1 Alcance')
    taverage02_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 2 Alcance')
    taverage03_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 3 Alcance')
    taverage04_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 4 Alcance')
    taverage05_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 5 Alcance')
    taverage06_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 6 Alcance')
    taverage07_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 7 Alcance')
    taverage08_reach = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 8 Alcance')

    taverage01_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 1 Impresiones')
    taverage02_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 2 Impresiones')
    taverage03_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 3 Impresiones')
    taverage04_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 4 Impresiones')
    taverage05_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 5 Impresiones')
    taverage06_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 6 Impresiones')
    taverage07_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 7 Impresiones')
    taverage08_impressions = fields.Integer(compute='_compute_averages', store=True, string='Cálculo media 8 Impresiones')
    
    # Campos para tasas de crecimiento entre medias de los registros inicial a final sin tener en cuenta los valores intermedios
    growthrate_engagement = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>F Vinculación')
    growthrate_interactions = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>F Interacciones')
    growthrate_reach = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>F Alcance')
    growthrate_impressions = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>F Impresiones')

    # Campos para tasas de crecimiento de 8 valores medios que tienen en cuenta todos los registros incluidos el inicial y el final en los cálculos
    growthrate_engagement_1_to_2 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 1>2 Vinculación')
    growthrate_engagement_2_to_3 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 2>3 Vinculación')
    growthrate_engagement_3_to_4 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 3>4 Vinculación')
    growthrate_engagement_4_to_5 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 4>5 Vinculación')
    growthrate_engagement_5_to_6 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 5>6 Vinculación')
    growthrate_engagement_6_to_7 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 6>7 Vinculación')
    growthrate_engagement_7_to_8 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 7>8 Vinculación')

    growthrate_interactions_1_to_2 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 1>2 Interacciones')
    growthrate_interactions_2_to_3 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 2>3 Interacciones')
    growthrate_interactions_3_to_4 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 3>4 Interacciones')
    growthrate_interactions_4_to_5 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 4>5 Interacciones')
    growthrate_interactions_5_to_6 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 5>6 Interacciones')
    growthrate_interactions_6_to_7 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 6>7 Interacciones')
    growthrate_interactions_7_to_8 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 7>8 Interacciones')

    growthrate_reach_1_to_2 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 1>2 Alcance')
    growthrate_reach_2_to_3 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 2>3 Alcance')
    growthrate_reach_3_to_4 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 3>4 Alcance')
    growthrate_reach_4_to_5 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 4>5 Alcance')
    growthrate_reach_5_to_6 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 5>6 Alcance')
    growthrate_reach_6_to_7 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 6>7 Alcance')
    growthrate_reach_7_to_8 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 7>8 Alcance')

    growthrate_impressions_1_to_2 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 1>2 Impresiones')
    growthrate_impressions_2_to_3 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 2>3 Impresiones')
    growthrate_impressions_3_to_4 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 3>4 Impresiones')
    growthrate_impressions_4_to_5 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 4>5 Impresiones')
    growthrate_impressions_5_to_6 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 5>6 Impresiones')
    growthrate_impressions_6_to_7 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 6>7 Impresiones')
    growthrate_impressions_7_to_8 = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 7>8 Impresiones')

    # Campos para tasas de crecimiento inicio-primera y última-fin
    growthrate_engagement_start_to_first = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>1 Vinculación')
    growthrate_engagement_last_to_end = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 8>F Vinculación')
    growthrate_interactions_start_to_first = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>1 Interacciones')
    growthrate_interactions_last_to_end = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 8>F Interacciones')
    growthrate_reach_start_to_first = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>1 Alcance')
    growthrate_reach_last_to_end = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 8>F Alcance')
    growthrate_impressions_start_to_first = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento I>1 Impresiones')
    growthrate_impressions_last_to_end = fields.Float(compute='_compute_averages', store=True, string='Tasa Crecimiento 8>F Impresiones')

    @api.model #ayuda a evitar errores timezone para hacer más robusto el módulo obteniendo el offset directamente desde el perfil del usuario
    def get_user_tz_offset(self):
        try:
            tz_offset = int(self.env.user.tz_offset)  # Asegurarse de que sea un entero
            return tz_offset
        except (ValueError, TypeError):
            return 0  # Valor predeterminado si hay algún problema

    # Cálculo de campos computados para las 8 medias respecto del tiempo comprendido entre la fecha del primer juego de datos y la fecha del ultimo juego de datos introducidos.
    @api.depends('smmonitor_tabs', 'firstdata_datetakesdata', 'latestdata_datetakesdata')
    def _compute_averages(self):
        for task in self:
            # Inicializar todas las tasas de crecimiento y promedios a None para evitar errores en el caso de que no haya datos suficientes.
            metricsanalyze =  ['engagement', 'reach', 'interactions', 'impressions']
            for metric in metricsanalyze:
                setattr(task, f'growthrate_{metric}', None)
                setattr(task, f'growthrate_{metric}_start_to_first', None)
                setattr(task, f'growthrate_{metric}_last_to_end', None)
                for i in range(1, 9):
                    setattr(task, f'taverage0{i}_{metric}', None)
                    if i < 8:
                        setattr(task, f'growthrate_{metric}_{i}_to_{i+1}', None)

            if task.firstdata_datetakesdata and task.latestdata_datetakesdata:
                start_date = task.firstdata_datetakesdata
                end_date = task.latestdata_datetakesdata
                total_days = (end_date - start_date).days
                if total_days > 0:
                    interval = total_days / 9
                    all_records = task.smmonitor_tabs.sorted(key=lambda r: r.datetakesdata)

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
                    
                    # Calcular tasas de crecimiento entre inicio a fin
                    for metric in metricsanalyze:
                        start_value = getattr(task, f'firstdata_{metric}')
                        end_value = getattr(task, f'latestdata_{metric}')
                        growthrate = self._calculate_growthrate(start_value, end_value) if start_value is not None and end_value is not None else 0
                        setattr(task, f'growthrate_{metric}', growthrate)

                    # Calcular tasas de crecimiento entre medias
                    for i in range(1, 8):
                        for metric in metricsanalyze:
                            start_value = getattr(task, f'taverage0{i}_{metric}')
                            end_value = getattr(task, f'taverage0{i+1}_{metric}')
                            growthrate = self._calculate_growthrate(start_value, end_value) if start_value is not None and end_value is not None else 0
                            setattr(task, f'growthrate_{metric}_{i}_to_{i+1}', growthrate)

                    # Calcular tasa de crecimiento entre valor inicial y primera media, y entre última media y valor final
                    for metric in metricsanalyze:
                        start_to_first = self._calculate_growthrate(getattr(task, f'firstdata_{metric}'), getattr(task, f'taverage01_{metric}')) if getattr(task, f'firstdata_{metric}') is not None and getattr(task, f'taverage01_{metric}') is not None else 0
                        last_to_end = self._calculate_growthrate(getattr(task, f'taverage08_{metric}'), getattr(task, f'latestdata_{metric}')) if getattr(task, f'taverage08_{metric}') is not None and getattr(task, f'latestdata_{metric}') is not None else 0
                        setattr(task, f'growthrate_{metric}_start_to_first', start_to_first)
                        setattr(task, f'growthrate_{metric}_last_to_end', last_to_end)
                else:
                    # Si no hay días en el intervalo, asignar valores por defecto
                    task.growthrate_engagement = 0
                    task.growthrate_interactions = 0
                    task.growthrate_reach = 0
                    task.growthrate_impressions = 0
            else:
                # Asegurarse de asignar valores por defecto si falta algún dato inicial
                task.growthrate_engagement = 0
                task.growthrate_interactions = 0
                task.growthrate_reach = 0
                task.growthrate_impressions = 0
                for metric in metricsanalyze:
                    setattr(task, f'growthrate_{metric}_start_to_first', 0)
                    setattr(task, f'growthrate_{metric}_last_to_end', 0)

    @api.model
    def _calculate_growthrate(self, start_value, end_value):
        if start_value == 0:
            return 100 if end_value > 0 else 0
        return ((end_value - start_value) / start_value) * 100

    @api.depends('smmonitor_tabs')
    def _compute_analytics_count(self):
        for task in self:
            task.analytics_count = len(task.smmonitor_tabs)

    @api.depends('temp_engagement', 'temp_interactions', 'temp_reach', 'temp_impressions')
    def _compute_can_add_analytics(self):
        for task in self:
            task.can_add_analytics = any([
                task.temp_engagement != 0,
                task.temp_interactions != 0,
                task.temp_reach != 0,
                task.temp_impressions != 0
            ])

    @api.depends('smmonitor_tabs', 'smmonitor_tabs.datetakesdata', 'smmonitor_tabs.engagement', 'smmonitor_tabs.interactions', 'smmonitor_tabs.reach', 'smmonitor_tabs.impressions')
    def _compute_latest_analytics(self):
        for task in self:
            latest_record = task.smmonitor_tabs.sorted('datetakesdata', reverse=True)[:1]
            task.latest_datetakesdata = latest_record.datetakesdata if latest_record else False
            task.latest_engagement = latest_record.engagement if latest_record else 0.0
            task.latest_interactions = latest_record.interactions if latest_record else 0
            task.latest_reach = latest_record.reach if latest_record else 0
            task.latest_impressions = latest_record.impressions if latest_record else 0

    @api.constrains('temp_datetakesdata', 'temp_engagement', 'temp_interactions', 'temp_reach', 'temp_impressions')
    def _check_temp_values(self):
        for task in self:
            tz_offset = int(self.env.user.tz_offset or 0)  # Obtenemos el offset desde el usuario y aseguramos de convertir a entero
            today = fields.Date.context_today(task) - timedelta(minutes=tz_offset)

            if task.temp_datetakesdata > today:
                raise ValidationError("La fecha no puede ser posterior al día de hoy.")
            if task.temp_datetakesdata < today - timedelta(days=365):
                raise ValidationError("La fecha no puede ser anterior a un año desde hoy.")
            if task.temp_engagement < 0 or task.temp_engagement > 999999.99:
                raise ValidationError("La vinculación debe estar entre 0% y 999999.99%.")
            if task.temp_interactions < 0:
                raise ValidationError("Las interacciones no pueden ser negativas.")
            if task.temp_reach < 0:
                raise ValidationError("El alcance no puede ser negativo.")
            if task.temp_impressions < 0:
                raise ValidationError("Las impresiones no pueden ser negativas.")

    def action_add_analytics(self):
        self.ensure_one()
        if self.can_add_analytics:
            self.env['project.task.smmonitor'].create({
                'smmonitor_task_id': self.id,
                'datetakesdata': self.temp_datetakesdata,
                'engagement': self.temp_engagement,
                'interactions': self.temp_interactions,
                'reach': self.temp_reach,
                'impressions': self.temp_impressions,
            })
            self.sudo().write({
                'temp_datetakesdata': fields.Date.context_today(self),
                'temp_engagement': 0,
                'temp_interactions': 0,
                'temp_reach': 0,
                'temp_impressions': 0,
            })
        else:
            raise ValidationError("No se pueden agregar análisis con todos los valores en cero.")
        
class SmmonitorProject(models.Model):
    _inherit = 'project.project'

    # Campo de selección para la Normalización de Vinculación
    engagement_normalization = fields.Selection(
        selection=[('100', '100'), ('1000', '1000'), ('10000', '10000')],
        string='Normalización de Vinculación',
        default='100',
        help="Selecciona el valor adecuado para ajustar y normalizar el cálculo de la Vinculación (Engagement), en base a la cantidad de seguidores que existan en la red social que vas a gestionar con este proyecto."
    )