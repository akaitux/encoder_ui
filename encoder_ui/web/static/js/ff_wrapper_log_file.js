var self_host = location.protocol+'//'+location.hostname+(location.port ? ':'+location.port: '');
var base_split = window.location.href.split('/');
var container = base_split[base_split.length - 3];
var file = base_split[base_split.length - 2];
var apiContainerLogsList = self_host + '/api/logs/' + container + '/' + file + '/';
var selfLogsPage = self_host + '/logs/ff_wrapper/' + container + '/';
var scrollSpeedVer = 20
var scrollSpeedHor = 10



function showError(msg, error) {
    console.log(error)
    errorEl = document.getElementById('error')
    errorEl.innerHTML = msg
};


function btnScrollTop(el) {
    el.scrollTop = 0;
    var btnScroll = document.getElementById('btnScroll')
    btnScroll.setAttribute("onclick", "btnScrollBottomBind()")
    btnScroll.innerHTML = "Bottom"
}

function btnScrollBottom(el) {
    el.scrollTop = el.scrollHeight;
    btnScroll.setAttribute("onclick", "btnScrollTopBind()")
    btnScroll.innerHTML = "Top"
    btnScroll.set
}

function btnPartialScrollBottom(el) {
    el.scrollTop += scrollSpeedVer
}

function btnPartialScrollTop(el) {
    el.scrollTop -= scrollSpeedVer;
}

function btnPartialScrollLeft(el) {
    el.scrollLeft -= scrollSpeedHor;
}

function btnPartialScrollRight(el) {
    el.scrollLeft += scrollSpeedHor;
}

function btnScrollTopBind() {
    el = document.getElementById('file_source');
    btnScrollTop(el)

}

function btnScrollBottomBind() {
    el = document.getElementById('file_source');
    btnScrollBottom(el)
}


function disableUpdateButton() {
    document.getElementById('btnUpdate').disabled = true;
    document.getElementById('btnUpdate').innerHTML= 'Loading...';
}


function enableUpdateButton() {
    document.getElementById('btnUpdate').disabled = false;
    document.getElementById('btnUpdate').innerHTML= 'Update';
}


function getLog() {
    disableUpdateButton()
    $.ajax({
            type: 'GET',
            url: apiContainerLogsList,
            data: $(this).serialize(),
            dataType: 'json',
            success: function (data) {
                var objDiv = document.getElementById("file_source");
                objDiv.innerHTML = '<pre>' + data.content + '</pre>'
                el = document.getElementById('file_source');
                btnScrollBottom(el)
            },
            error: function (error) {
                switch (error.status) {
                    case 400:
                        showError('No container name or file name in request. Response error', error);
                        break
                    case 404: 
                        showError('File not found', error);
                        break
                    case 500: 
                        showError("Access denied", error);
                        break
                }
            },
            complete: function () {
                enableUpdateButton();
            }
    });
}


var selfLink = document.getElementById("self_link");
selfLink.setAttribute("href", window.location.href)

var selfLogs = document.getElementById("self_logs");
selfLogs.setAttribute("href", selfLogsPage)

getLog()


$(document).keydown(function(e) {
    el = document.getElementById('file_source');
    // partial scroll left - h
    if (e.keyCode == 72 || e.keyCode == 37) {
        btnPartialScrollLeft(el)
    }

    // partial scroll right - l
    if (e.keyCode == 76 || e.keyCode == 39) {
        btnPartialScrollRight(el)
    }

    // partial scroll up - k
    if (e.keyCode == 75 || e.keyCode == 38) {
        btnPartialScrollTop(el)
    }

    // partial scroll down - j
    if (e.keyCode == 74 || e.keyCode == 40) {
        btnPartialScrollBottom(el)
    }

    // full scroll up - g
    if (e.keyCode == 71 && e.shiftKey === false) {
        btnScrollTop(el)
    }

    // full scroll down - G
    if (e.keyCode == 71 && e.shiftKey === true) {
        btnScrollBottom(el)
    }

    // update - r
    if (e.keyCode == 82) {
        getLog(el)
    }

});
