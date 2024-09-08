/**#######################################################################################################################################################
#
#    Infinity Draw.
#
#    Copyright (C) 2024-HOY Infinity Draw (<https://infinitydraw.es>)
#    Autor: Fernan Nerd (<https://infinitydraw.es>)
#
#    Puedes modificarlo bajo los términos de GNU LESSER.
#    LICENCIA PÚBLICA GENERAL (LGPL v3), Versión 3.
#
#    Este programa se distribuye con la esperanza de que sea útil,
#    pero SIN NINGUNA GARANTÍA; sin siquiera la garantía implícita de
#    COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR.  Ver el
#    LICENCIA PÚBLICA GENERAL MENOR GNU (LGPL v3) para más detalles.
#
#    Debería haber recibido una copia de la LICENCIA PÚBLICA GENERAL MENOR DE GNU
#    (LGPL v3) junto con este programa.
#    En caso contrario, consulte <http://www.gnu.org/licenses/>.
#
##########################################################################################################################################################
#
#       Los principales archivos del módulo son __manifest__-1.8.py, timezone_detector-1.3.js (con cookie) y
#       timezone_detector-1.4.js (con metodo de odoo) incluyen el para detectar la hora del usuario local.
#       El metodo de la cookie NO funcione correctamente en el navegador, pero si como módulo como tal.
#       El metodo de odoo funciona funciona correctamente tanto en el navegador como el módulo como tal.
#       El archivo smmonitor_views.3.0.xml (con cookie) para las vistas y el archivo smmonitor_views.3.1.xml (con metodo Odoo)
#       para las vistas, donde en este caso anulamos el campo 'user_timezone_offset' ya que deja de ser necesario.
#       El archivo de python smmonitor_model-3.0.py (con cookie) y el mismo terminado en 3.1.py (con metodo odoo) son los
#       que incluyen toda la lógica del módulo para hacer que todo se cree correctamente, siempre teniendo en cuenta lo que
#       hemos comentado y es que el metodo de la cookie no termina de funcionar ocasionando un error en el navegador web aunque
#       si funciona el módulo como tal, y el metodo que odoo recomienda implementar funciona correctamente en todos los sentidos,
#       teniendo en cuenta que en este metodo se quita el campo 'user_timezone_offset' ya que deja de ser necesario.
#
########################################################################################################################################################## **/

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