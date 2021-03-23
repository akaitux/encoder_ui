var self_host = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');
var  getContainersTableInterval = 5000
var  getResourcesInterval = 5000
var scrollSpeedVer = 20
var scrollSpeedHor = 10

var currentPopupId= ''


function hidePopup() {
    $('.overlay_popup, .popup_docker_logs, .popup_docker_cmd').hide(); 

}


function scrollTop(el) {
    el.scrollTop = 0;
}


function scrollBottom(el) {
    el.scrollTop = el.scrollHeight;
}


function partialScrollBottom(el) {
    el.scrollTop += scrollSpeedVer;
}


function partialScrollTop(el) {
    el.scrollTop -= scrollSpeedVer;
}


function partialScrollLeft(el) {
    el.scrollLeft -= scrollSpeedHor;
}


function partialScrollRight(el) {
    el.scrollLeft += scrollSpeedHor;
}



function setPopupLogs(popupId, logs) {
    var div = document.getElementById(popupId)
    if (! div) {
        div = document.createElement("div");
        $(div).attr('id', popupId);
        $(div).attr('class', 'popup_docker_logs');
        $('#popup_logs').append(div);
    }
    var divText = '';
    var divText = '<pre>' + logs + '</pre>'
    var div = document.getElementById(popupId);
    div.innerHTML = divText;
    div.scrollTop = div.scrollHeight
}

function setPopupCmd(popupId, cmd) {
    var div = document.getElementById(popupId)
    if (! div) {
        div = document.createElement("div");
        $(div).attr('id', popupId);
        $(div).attr('class', 'popup_docker_cmd');
        $('#popup_cmd').append(div);
    }
    var divText = '';
    var divText = '<pre>' + cmd + '</pre>'
    var div = document.getElementById(popupId);
    div.innerHTML = divText;
}

function genContainerGpuUsage(item) {
    var gpu_name = "";
    if (item.gpu_name) {
        var gpu_name =  item.gpu_name + ' (id: ' + item.gpu_index + ')';
    }
    result = '<td class="gpu_usage" title="' + gpu_name + '">'
    if (item.gpu_index) {
        result += '(id: ' + item.gpu_index + ') '
    }
    if ('gpu_usage_enc' in item) {
        if (item.gpu_usage_enc === '' || ! item.gpu_usage_enc) {
            result += '-'
        } else {
            result += item.gpu_usage_enc + '%'
        }
    }
    result += ' | '
    if ('gpu_usage_dec' in item) {
        if (item.gpu_usage_dec === '' || ! item.gpu_usage_dec) {
            result += '-'
        } else {
            result += item.gpu_usage_dec + '%'
        }
    }
    result += ' | '
    if ('gpu_usage_mem' in item) {
        if (item.gpu_usage_mem === '' || ! item.gpu_usage_mem) {
            result += '-'
        } else {
            result += item.gpu_usage_mem + '%'
        }
    }
    result += '</td>';
    return result
}


function renderContainersTable(data) {
    var trHTML = $('#containers_table tbody tr:first-child').html();
    $.each(data.containers, function (i, item) {
        if (!('id' in item)) {
            return;
        }
        is_ff_wrapper = false;
        if (('ff_wrapper' in item) && item.ff_wrapper) {
            is_ff_wrapper = true;
        }
        var popupCmdId = 'popup_cmd_' + item.name 
        trHTML += '<tr><td><a class="docker_cmd_link" rel="' + popupCmdId + '">' + item.name + '</a></td>';
        trHTML += '<td>' + item.id.substring(0,8) + '</td>';
        trHTML += '<td>' + item.image + '</td>'
        if (item.status === "running") {
            trHTML += '<td class="container_state green_status" title="' + item.status + '">' + item.status[0] + '</td>'
        } else {
            trHTML += '<td class="container_state red_status" title="' + item.status + '">' + item.status[0] + '</td>'
        }
        if (is_ff_wrapper === true) {
            trHTML += '<td class="is_ff_wrapper_td">Yes</td>'
        } else {
            trHTML += '<td class="is_ff_wrapper_td">No</td>'
        }
        trHTML += '<td class="restart_count">' + item.restart_count + '</td>'
        trHTML += '<td class="up">' + item.up + '</td>'
        if (item.cpu_usage) {
            trHTML += '<td class="cpu_usage">' + item.cpu_usage + '%</td>'
        }
        else {
            trHTML += '<td></td>'
        }
        trHTML += genContainerGpuUsage(item)
        var popupLogsId =  'popup_logs_' + item.name 
        trHTML += '<td class="docker_logs_button_td" ><button class="docker_logs_button" rel="' + popupLogsId + '">show</button>'
        if (is_ff_wrapper === true) {
            trHTML += '<td class="ffmpeg_logs_td"><a class="ffmpeg_logs_link" href=/logs/ff_wrapper/' + item.name + '/>show</a>'
        } else {
            trHTML += '<td></td>'
        }
        trHTML += '</tr>'
        if (item.last_log) {
            setPopupLogs(popupLogsId, item.last_log);
        }
        if (item.cmd) {
            setPopupCmd(popupCmdId, item.cmd)
        }
    });
    $('#containers_table').html('<tbody>' + trHTML + '</tbody>');
    $('#updated_at').html(data.updated_at);
}

function getContainersTable() {
    $.ajax({
            type: 'GET',
            url: self_host + '/api/containers/', 
            data: $(this).serialize(),
            dataType: 'json',
            success: function (data) {
                renderContainersTable(data);
            },
            complete: function (data) {
                    setTimeout(getContainersTable, getContainersTableInterval);
            },
            error: function (data) {
                $('#updated_at').html('<p style="color: red">Ошибка, таблица не обновлена</p>')
            }
    });
}


function renderResources(data) {
    resources = data.resources
    var html = '<p>cpu la ';
    for (let el of resources.cpu_load_avg) {
        html += el.toFixed(1) + ' '
    }
    html += ' (' + resources.cores + ' cores)'
    html += '<span class="header_separator"></span>';
    html += 'mem used: ' + (resources.mem.used/1024).toFixed(1) + ' mb '
    html += ' (' + resources.mem.used_percent + '%)'
    html += '<span class="header_separator"></span>';
    html += 'gpu '
    var i = 1;
    // blue, green, orange, blue, purple
    var colors = ["#2e8af2", "#2ef24b", "#2ef2e2", "#f22ee2", "#d5f22e", "#2ef2ad", "#762ef2", "#2ef266"];
    if (resources.gpu) {
        for (let gpu of resources.gpu) {
            var color = ""
            if ((gpu.index) < colors.length) {
                color = colors[gpu.index]
            } else {
                var random = Math.floor(Math.random() * colors.length);
                color = colors[random];
            }
            html += '<span title="' + gpu.name + '" style="border-bottom: 1px solid ' + color + '">'
            html += 'id: ' + gpu.index
            html += ' enc: ' + gpu['utilization.gpu.enc'] + '% dec: ' + gpu['utilization.gpu.dec']
            html += '% mem used: ' + gpu['utilization.memory'] + '%'
            html += "</span>"
            if (i !== resources.gpu.length) {
                html += ',  '
            }
            i += 1;
        }
    }
    document.getElementById('header_right').innerHTML = html;
}


function getResources() {
    $.ajax({
        type: 'GET',
        url: self_host + '/api/resources/', 
        data: $(this).serialize(),
        dataType: 'json',
        success: function (data) {
           renderResources(data)
        },
        complete: function (data) {
            setTimeout(getResources, getResourcesInterval);
        },
        error: function (err) {
            console.log('error while getting resources')
        }
    })
};



// MAIN //

getContainersTable();
getResources();

$(document).on('click', '.docker_logs_button', function() {
    currentPopupId = $(this).attr("rel");
    var popupId = $('#' + $(this).attr("rel"));
    $(popupId).show();
    $('.overlay_popup').show();
})

$(document).on('click', '.docker_cmd_link', function() {
    currentPopupId = $(this).attr("rel");
    var popupId = $('#' + $(this).attr("rel"));
    $(popupId).show();
    $('.overlay_popup').show();
})


$('.overlay_popup').on('click', function() { 
    currentPopupId = '';
    hidePopup();
})

$(document).keydown(function(e) {
    if (! currentPopupId) {
        return
    }
    // ESCAPE key pressed
    if (e.keyCode == 27) {
        hidePopup();
    }

    var popup = document.getElementById(currentPopupId)
    // partial scroll left - h
    if (e.keyCode == 72 || e.keyCode == 37) {
        partialScrollLeft(popup)
    }

    // partial scroll right - l
    if (e.keyCode == 76 || e.keyCode == 39) {
        partialScrollRight(popup)
    }

    // partial scroll up - k
    if (e.keyCode == 75 || e.keyCode == 38) {
        partialScrollTop(popup)
    }

    // partial scroll down - j
    if (e.keyCode == 74 || e.keyCode == 40) {
        partialScrollBottom(popup)
    }

    // full scroll up - g
    if (e.keyCode == 71 && e.shiftKey === false) {
        scrollTop(popup)
    }

    // full scroll down - G
    if (e.keyCode == 71 && e.shiftKey === true) {
        scrollBottom(popup)
    }
});

