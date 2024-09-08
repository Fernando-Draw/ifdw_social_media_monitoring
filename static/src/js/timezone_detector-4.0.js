/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";

class TimezoneDetector {
    setup() {
        this.detectAndSetTimezone();
    }

    detectAndSetTimezone() {
        // Obtener el desplazamiento de la zona horaria en minutos
        const offset = -(new Date().getTimezoneOffset());
        const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        // Llamada al servidor para guardar el offset y la zona horaria
        this.env.services.rpc("/web/dataset/call_kw/project.task/save_tz_offset", {
            model: 'project.task',
            method: 'save_tz_offset',
            args: [[], { 'offset': offset, 'timezone': timezone }],
        }).catch(error => {
            console.error("Error al guardar el desplazamiento de zona horaria:", error);
        });
    }
}

export const timezoneDetector = {
    dependencies: ['rpc'],
    start(env) {
        const detector = new TimezoneDetector();
        detector.env = env;
        detector.setup();
    },
};

registry.category("services").add("timezoneDetector", timezoneDetector);