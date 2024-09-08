/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";

class CopyHashtags {
    async copyHashtagsToClipboard() {
        try {
            const response = await this.env.services.rpc('/web/dataset/call_kw/project.task/action_copy_hashtags', {
                model: 'project.task',
                method: 'action_copy_hashtags',
                args: [this.env.context.active_id],
            });

            // Copiar el texto al portapapeles usando la API Clipboard
            await navigator.clipboard.writeText(response);
            alert('Hashtags copiados al portapapeles.');
        } catch (error) {
            console.error("Error al copiar hashtags:", error);
            alert('Error al copiar hashtags.');
        }
    }
}

export const copyHashtags = {
    dependencies: ['rpc'],
    start(env) {
        const copyHashtagsInstance = new CopyHashtags();
        copyHashtagsInstance.env = env;
        document.querySelector('.btn-primary-copy-hashtags').addEventListener('click', () => {
            copyHashtagsInstance.copyHashtagsToClipboard();
        });
    },
};

registry.category("services").add("copyHashtags", copyHashtags);
