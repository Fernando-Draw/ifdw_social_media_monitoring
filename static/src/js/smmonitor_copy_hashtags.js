/** @odoo-module **/

import { registry } from "@web/core/registry";

function smmonitorCopyHashtags(env, action) {
    const content = action.params.content;
    navigator.clipboard.writeText(content).then(
        () => {
            console.log('Contenido copiado al portapapeles');
        },
        (err) => {
            console.error('No se pudo copiar el contenido: ', err);
            env.services.notification.notify({
                title: env._t("Error"),
                message: env._t("No se pudo copiar el contenido al portapapeles."),
                type: 'danger',
            });
        }
    );
}

registry.category("actions").add("smmonitor_copy_hashtags", smmonitorCopyHashtags);
