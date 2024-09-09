/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";

class CopyHashtagsComponent extends Component {

    static template = xml`<div>
        <button t-on-click="copyHashtags">Copiar Hashtags</button>
    </div>`;

    // Método para copiar los hashtags cuando el botón es clickeado
    async copyHashtags() {
        const { hashtags } = this.props;

        try {
            // Usa la API moderna del portapapeles para copiar el texto
            await navigator.clipboard.writeText(hashtags);
            alert('Hashtags copiados con éxito!');
        } catch (err) {
            console.error('No se pudieron copiar los hashtags', err);
            alert('No se pudieron copiar los hashtags.');
        }
    }
}

// Registro del componente dentro del sistema de acciones
registry.category('actions').add('copy_hashtags_action', CopyHashtagsComponent);


