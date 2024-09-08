/** @odoo-module **/

import { Component } from "@odoo/owl";  
import { registry } from "@web/core/registry";

class CopyHashtagsComponent extends Component {
    // Método que se ejecuta cuando el componente se carga
    async willStart() {
        const { hashtags } = this.props;

        // Crea un textarea temporal para copiar el texto al portapapeles
        const tempInput = document.createElement('textarea');
        tempInput.value = hashtags;
        document.body.appendChild(tempInput);
        tempInput.select();

        try {
            // Copia el texto al portapapeles
            const successful = document.execCommand('copy');
            const msg = successful ? 'Hashtags copied successfully!' : 'Unable to copy hashtags.';
            alert(msg);
        } catch (err) {
            console.error('Unable to copy', err);
        }

        // Elimina el textarea temporal después de copiar
        document.body.removeChild(tempInput);
    }
}

// Registro del componente dentro del sistema de acciones
registry.category('actions').add('copy_hashtags_action', CopyHashtagsComponent);
