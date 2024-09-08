odoo.define('ifdw_social_media_monitoring.timezone_detector', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');

    function detectAndSetTimezone() {
        var offset = -(new Date().getTimezoneOffset());
        document.cookie = "tz_offset=" + offset + ";path=/";

        // Opcionalmente, llama a un método del servidor para guardar el offset
        session.rpc("/web/dataset/call_kw/project.task/sudo/save_tz_offset", {
            model: 'project.task',
            method: 'save_tz_offset',
            args: [[], {'offset': offset}],
            kwargs: {},
        });
    }

    // Ejecuta la función cuando se carga la página
    core.bus.on('web_client_ready', detectAndSetTimezone);
});
