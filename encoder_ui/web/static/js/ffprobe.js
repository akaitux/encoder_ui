var apiFFProbeURL = '/api/ffprobe/'


function disableSendButton() {
    document.getElementById('address_btn').disabled = true;
    document.getElementById('address_btn').innerHTML= '...';
}


function enableSendButton() {
    document.getElementById('address_btn').disabled = false;
    document.getElementById('address_btn').innerHTML= 'run';
}

function showError(msg, error) {
    console.log(error)
    errorEl = document.getElementById('error')
    errorEl.innerHTML = msg
}


function onclickFFProbe() {
    var addr = document.getElementById('address_input').value
    doFFProbe(addr)
}


function renderPrograms(programs) {
    html = '';
    for (let program of programs) {
        html += '<div class="program">'
            html += '<div class="program_describe">'
                html += '<table>'
                    html += '<tr><td>program ID</td><td>' + program.program_id + '</td></th>'
                    html += '<tr><td>program num</td><td>' + program.program_num + '</td></th>'
                    if ('tags' in program) {
                        if ('service_name' in program.tags ) {
                            html += '<tr><td>service name</td><td>' + program.tags.service_name + '</td></th>'
                        }
                        if ('service_provider' in program.tags) {
                            html += '<tr><td>service provider</td><td>' + program.tags.service_provider + '</td></th>'
                        }
                    }
                    html += '<tr><td>num of streams</td><td>' + program.nb_streams + '</td></th>'
                    html += '<tr><td>PCR PID</td><td>' + program.pcr_pid+ '</td></th>'
                    html += '<tr><td>PMT PID</td><td>' + program.pmt_pid+ '</td></th>'
                html += '</table>'
            html += '</div>' // end div class="program_describe"
            if ('streams' in program) {
                html += '<div class="program_streams">'
                    html += '<h1>Streams</h1>'
                    html += renderStreams(program.streams)
                html += '</div>' // end div class="program_streams"
            }
        html += '</div>' // end div class="program"
    }
    return html
}


function hexToDec(hex) {
    hex = parseInt(hex, 16)
    return hex.toString(10); 
}


function renderStreams(streams) {
    html = '';
    for (let stream of streams) {
        html += '<div class="stream">'
            if (stream.codec_type && stream.codec_type === 'video') {
                html += '<table class="table_video_stream">'
            } else if (stream.codec_type && stream.codec_type === 'audio') {
                html += '<table class="table_audio_stream">'
            } else {
                html += '<table>'
            }
                if (stream.id) {
                    html += '<tr><td>stream id</td><td>' + stream.id + ' (' + hexToDec(stream.id) + ')</td></th>'
                }
                html += '<tr><td>stream index</td><td>' + stream.index + '</td></th>'
                html += '<tr><td>codec</td><td>' + stream.codec_name+ '</td></th>'
                html += '<tr><td>codec type</td><td>' + stream.codec_type+ '</td></th>'
                if ('tags' in stream && 'variant_bitrate' in stream.tags) {
                    html += '<tr><td>playlist variant bitrate</td><td>' + stream.tags.variant_bitrate + '</td></th>'
                }
                if (stream.codec_type === 'video') {
                    html += '<tr><td>color</td><td>' + stream.color_space+ '</td></th>'
                    html += '<tr><td>pix_fmt</td><td>' + stream.pix_fmt+ '</td></th>'
                    html += '<tr><td>size</td><td>' + stream.width + 'x' + stream.height + '</td></th>'
                    html += '<tr><td>aspect</td><td>' + stream.display_aspect_ratio+ '</td></th>'
                    html += '<tr><td>level</td><td>' + stream.level+ '</td></th>'
                    html += '<tr><td>profile</td><td>' + stream.profile + '</td></th>'
                    html += '<tr><td>refs</td><td>' + stream.refs + '</td></th>'
                    html += '<tr><td>bits per raw sample</td><td>' + stream.bits_per_raw_sample + '</td></th>'
                    html += '<tr><td>fps</td><td>' + stream.r_frame_rate + '</td></th>'
                    if ('field_order' in stream && stream.field_order == 'progressive') {
                        html += '<tr><td>field order</td><td>' + stream.field_order+ '</td></th>'
                    } else {
                        html += '<tr><td>field order</td><td>interlaced</td></th>'
                    }
                } else if (stream.codec_type === 'audio') {
                    html += '<tr><td>bitrate</td><td>' + stream.bit_rate+ '</td></th>'
                    html += '<tr><td>sample rate</td><td>' + stream.sample_rate + '</td></th>'
                    html += '<tr><td>channel layout</td><td>' + stream.channel_layout + '</td></th>'
                    html += '<tr><td>channels</td><td>' + stream.channels + '</td></th>'
                    if ('tags' in stream && 'language' in stream.tags ) {

                       html += '<tr><td>language</td><td>' + stream.tags.language + '</td></th>'
                    } else {
                       html += '<tr><td>language</td><td>None</td></th>'
                    }
                }
            html += '</table>'
        html += '</div>' // end div class=stream
    }
    return html
}


function showStreams(data) {
    info_wrapper = document.getElementById('ffprobe_info_wrapper')
    info_wrapper.innerHTML = ''
    html = '';
    if ("programs" in data && data.programs.length > 0) {
        html += '<div id="programs_div"><h1>Programs</h1>' + renderPrograms(data.programs) + '</div>'
    }
    if ("streams" in data && data.streams.length > 0) {
        html += '<div id="standalone_streams_div"><h1>Standalone streams</h1>' + renderStreams(data.streams) + '</div>'
    }
    info_wrapper.innerHTML = html;
    document.getElementById('source').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>'
}

function toggleSource() {
    source = document.getElementById('source');
    button = document.getElementById('show_source')
    if (source.hidden === true) {
        source.hidden = false;
        button.innerHTML = 'Hide source'
    } else {
        source.hidden = true;
        button.innerHTML = 'Show source'
    }
}

function cleanup() {
    document.getElementById('error').innerHTML = ""
    document.getElementById('ffprobe_info_wrapper').innerHTML = ""
    document.getElementById('source').innerHTML = ""
    document.getElementById('source').hidden = true
    document.getElementById('show_source').hidden = true
    document.getElementById('show_source').innerHTML = 'Show source'
}


function doFFProbe(addr) {
    disableSendButton()
    cleanup()
    $.ajax({
            type: 'POST',
            url: apiFFProbeURL,
            data: {addr: addr},
            dataType: 'json',
            success: function (data) {
                showError('');
                showStreams(data);
                document.getElementById('show_source').hidden = false;
            },
            error: function (error) {
                showError(error.responseJSON.error);
            },
            complete: function() {
                enableSendButton();
            }

    });
}


$(document).keydown(function(e) {
    // Enter key pressed
    if (e.keyCode == 13) {
        onclickFFProbe();
    }
})