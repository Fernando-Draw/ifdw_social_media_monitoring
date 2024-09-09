/** @odoo-module **/

import { Component, onMounted, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class CopyHashtagsComponent extends Component {
    setup() {
        this.notification = useService('notification');
    }
    static template = xml`
    <div>
        <button t-on-click="copyHashtags">Copiar Hashtags</button>
    </div>`;

    // Método para copiar los hashtags cuando el botón es clickeado
    async copyHashtags() {
        try {
            // Usa la API moderna del portapapeles para copiar el texto
            await navigator.clipboard.writeText(this.props.hashtags);
            this.showSuccessMessage();
        } catch (err) {
            this.showErrorMessage();
            console.error('No se pudieron copiar los hashtags', err);
        }
    }
    showSuccessMessage() {
        this.notification.add('Hashtags copiados con éxito', {
            type: 'success',
            sticky: false
        });
    }
    showErrorMessage() {
        this.notification.add('No se pudieron copiar los hashtags', {
            type: 'danger',
            sticky: false
        });
    }
}

// Registro del componente dentro del sistema de acciones
registry.category('actions').add('copy_hashtags_action', CopyHashtagsComponent);


