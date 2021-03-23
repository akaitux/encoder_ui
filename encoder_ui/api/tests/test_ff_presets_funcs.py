from encoder_ui.api.ff_presets_funcs import compile_ff_preset

VIDEO_PRESET_DICT = {
    'name': 'fullhd_test',
    'aspect': '16:9',
    'bf': 2,
    'bitrate': '200k',
    'codec': 'tratata',
    'crf': 25,
    'fps': 20,
    'gop': 250,
    'maxrate': '25m',
    'preset': 'high',
    'profile': 'baseline',
    'level': 3.0,
    'qscale': 1,
    'refs': 1,
    'size': '1920x1080',
    'vframes': 20,
    'force_key_frames': "expr:gte(t,n_forced*2)",
    'forced-idr': True,
    'x264_params': [
        {'level': '31'},
        {'ref': 3},
        "no-scenecut",
        {'vbv_maxrate': 6096},
    ],
    'x265_params': [
        {'level': '31'},
        {'ref': 3},
        "no-scenecut",
        {'vbv_maxrate': 6096},
    ],
    'filter_chains': [
        {
            'name': 'chain1',
            'filters': [
                {
                    'name': 'yadif',
                    'values': [0, 0, 0]
                },
                {
                    'name': 'drawtext',
                    'values': [{'text': 'hey'}]
                },
                'pullup',
            ],
        },
        {
            'name': 'chain2',
            'filters': [
                "some_filter"
            ]
        }
    ],
    'rc': 'vbr_hq',
    'rc-lookahead': 32,
    'cq': 20,
    'zerolatency': True,
    'spatial-aq': 1,
    'aq-strength': 12,
    'coder': 'cabac',
}

AUDIO_PRESET_DICT = {
    'name': 'aac_128k',
    'bitrate': '128k',
    'codec': 'libfdk_aac',
    'sample_rate': 44100,
    'ac': 1,
}

STREAM_PRESET_DICT = {
    'ffmpeg_params': [
        'deinterlace',
        {'fflags': '+genpts'},
    ],
    'hwaccel': 'cuda',
    'input': [
        {'addr': 'http://input', 'maps': ['0', {'0': 0}, {'0': 'v'}, {'0': 'p:1344'}, {'i': '0x401'}]},
        'http://...'

    ],
    'output': [
        {
            'video_preset': VIDEO_PRESET_DICT,
            'audio_preset': AUDIO_PRESET_DICT,
            'format': 'flv',
            'outputs': [
                {
                    'select': 'v:0,a',
                    'addr': 'local0',
                    'onfail': 'ignore',
                },
                {
                    'select': 'v:0,a',
                    'format': 'flv',
                    'addr': 'rtmp://server0/app/instance',
                }
            ],
            'hls_params': {
                'hls_param1': 123,
                'hls_param2': 456
            }
        }
    ]
}


def test_compile():
    stream, errors = compile_ff_preset(STREAM_PRESET_DICT)
    assert errors is None
    assert stream is not None
    assert stream.cmd != None
    assert stream.cmd.startswith('-deinterlace -fflags')
    assert stream.is_valid is True
    