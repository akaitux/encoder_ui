var self_host = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');
var container = window.location.href.split('/')
container = container[container.length - 2]
var getLogsTimeout = 100
var apiContainerLogsList = self_host + '/api/logs/' + container + '/'


function showError(msg, error) {
    console.log(error)
    errorEl = document.getElementById('error')
    errorEl.innerHTML = msg
}

function addLogsRow(log_items) {
    var result = '';
    $.each(log_items, function (i, item) {
        if (!('dt' in item)) {
            return;
        }
        result += '<tr>'
        result += '<td>' + item.dt + '</td>';
        result += '<td><a class="file_link" href="/logs/ff_wrapper/' + container + '/' + item.filename + '/">' + item.filename + '</a></td>';
        result += '</tr>'
    })
    return result 
}


function getLogs() {
    $.ajax({
            type: 'GET',
            url: apiContainerLogsList,
            data: $(this).serialize(),
            dataType: 'json',
            success: function (data) {
                if ("manager" in data) {
                    var trHTML = ''
                    trHTML += addLogsRow(data.manager);
                    var objDiv = document.getElementById("logs_manager_table_tbody");
                    objDiv.innerHTML = trHTML;
                }
                if ("ffmpeg" in data) {
                    var trHTML = ''
                    trHTML += addLogsRow(data.ffmpeg);
                    var objDiv = document.getElementById("logs_ffmpeg_table_tbody");
                    objDiv.innerHTML = trHTML;
                }
            },
            error: function (error) {
                switch (error.status) {
                    case 400:
                        showError('No container name in request, error in response', error);
                        break
                    case 404: 
                        showError('Container logs dir not found', error);
                        break
                    case 500: 
                        showError("Main logs directory (/var/log/ffmpeg/) doesn't exists, server error", error);
                        break
                }
            }
    });
}

var selfLink = document.getElementById("self_link");
selfLink.setAttribute("href", window.location.href)

getLogs()