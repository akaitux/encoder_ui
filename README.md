

## API


[GET /api/resources/](#get-/api/resources/)

[GET /api/containers/](#get-/api/containers/)

[GET /api/logs/<container_name>/](#get-/api/logs/<container_name>/)

[GET /api/logs/<container_name>/<file_name>](#get-/api/logs/<container_name>/<file_name>)

[POST /api/ffprobe/](#post-/api/ffprobe/)

[POST /api/ffprobe/compile/](#post-/api/ffprobe/compile/)


### GET /api/resources/

Returned cpu, mem, gpu stats

#### Responses

**200 json**

```javascript
{
  "resources": {
    "cpu_load_avg": [
      1.3916015625,
      1.48876953125,
      1.5
    ],
    "mem": {
      "total": 32814120, # kbytes
      "available": 26712508, # kbytes
      "used": 6101612, # kbytes
      "used_percent": 18, 
      "available_percent": 82
    },
    "gpu": [
      {
        "driver_version": "440.100",
        "name": "Tesla T4",
        "uuid": "GPU-bbd3f1b1-660a-44b0-911f-169e11579607",
        "pci.bus_id": "00000000:AF:00.0",
        "fan.speed": "",
        "pstate": "P0",
        "memory.total": "15109", # mbytes
        "memory.used": "2003", # mbytes
        "memory.free": "13106", # mbytes
        "utilization.memory": "9",
        "utilization.gpu": "36",
        "temperature.gpu": "45",
        "utilization.gpu.enc": "51",
        "utilization.gpu.dec": "10",
        "utilization.gpu.sm": "36",
        "power": "34",
        "index": "0"
      }
    ]
  },
  "updated_at": "2020-10-28 16:48:09"
}
```

**500 - Internal error***

Example:

```javascript
    {'error': 'Undefined exception'}
```

### GET /api/containers/

Returned all containers if the container image contains 'ffmpeg' or 'ffw-ffmpeg'. In second case, container's info contains 'ff_wrapper' dict with params (see Example)

#### GET Parameters: 

only_ffw - bool, default=False, return only containers with ff_wrapper

#### Responses:

**200 - json with containers.**

Example: 

```javascript
{
  "containers": [
    {
      "name": "elated_hofstadter",
      "id": "d4c9635ce3cdf0c8be998c8b1e51337e7e4aaf214b70b2f20c4454a339209489",
      "status": "running",
      "last_log": "2020-10-28T13:49:56.652494207Z Warning - python lower than 3.7 and HTTP Server running in one-thread mode\r\n2020-10-28T13:49:56.677083929Z [2020-10-28 13:49:56 UTC] FFMpeg progress thread started\r\n2020-10-28T13:49:56.677286729Z [2020-10-28 13:49:56 UTC] FFMpeg stdout thread started\r\n2020-10-28T13:49:56.677292330Z [2020-10-28 13:49:56 UTC] Logs - /var/log/ffmpeg/ff_wrapper_elated_hofstadter\r\n2020-10-28T13:49:56.677626567Z [2020-10-28 13:49:56 UTC] FFMpeg logs writer thread started\r\n2020-10-28T13:50:01.684515513Z [2020-10-28 13:50:01 UTC] Manager thread started (with delay 5s)\r\n2020-10-28T13:50:01.696746714Z [2020-10-28 13:50:01 UTC] Encoding checker will be started in 55s ...\r\n",
      "started_at": "2020-10-28T13:49:56.593543865Z",
      "finished_at": "0001-01-01T00:00:00Z",
      "finished_at_formatted": "",
      "up": "0d:0h:0m:37s",
      "image": "hub.docker.com/hidnoiz/ffw-ffmpeg-nvidia/ffw-ffmpeg-nvidia:4.2.4_10.2_0.2.0",
      "ff_wrapper": {
        "CONTAINER_ID": "d4c9635ce3cdf0c8be998c8b1e51337e7e4aaf214b70b2f20c4454a339209489",
        "CONTAINER_NAME": "elated_hofstadter",
        "ENABLE_HTTP_SERVER": "0",
        "ENCODING_CHECK_START_DELAY": "55",
        "ENCODING_DELTA_FPS": "10",
        "ENCODING_DELTA_SPEED": "0.2",
        "ENCODING_DISABLE_CHECK": "False",
        "ENCODING_MAX_ERROR_TIME": "10",
        "ENCODING_MAX_STDOUT_STUCK_TIME": "15",
        "ENCODING_MIN_BASE_FPS": "14.0",
        "ENCODING_MIN_SPEED": "0.8",
        "FFMPEG_PID": "6",
        "HTTP_HOST": "localhost",
        "HTTP_PORT": "9800",
        "IS_DEBUG": "False",
        "LOGS_PATH": "/var/log/ffmpeg/ff_wrapper_elated_hofstadter",
        "LOGS_PATH_BASE": "/var/log/ffmpeg/",
        "LOG_ROTATION_BACKUP": "3",
        "LOG_ROTATION_DAYS": "3",
        "LOG_ROTATION_MAX_KBYTES": "25000",
        "LOG_ROTATION_MODE": "days",
        "MANAGER_START_DELAY": "5",
        "NO_FILE_LOG": "False",
        "PID": "1",
        "PROGRESS_BUFFER_LEN": "100000",
        "PROGRESS_FIFO_PATH": "/tmp/ff_wrapper/pipes/",
        "STATUS_PATH": "/tmp/ff_wrapper/status/",
        "STDOUT_BUFFER_LEN": "100000",
        "WORKDIR": "/tmp/ff_wrapper"
      },
      "cmd": "-i http://rtmp-server.dom:1935/spas -vcodec h264 -b:v 1M -maxrate 1M -bufsize 2M -y -f flv /dev/null",
      "base_pid": 127792,
      "ffmpeg_pid": "127815",
      "created": "2020-10-28T13:49:56.214865429Z",
      "restart_count": 0,
      "is_host_network": true,
      "gpu_usage_enc": "23",
      "gpu_usage_dec": "2",
      "gpu_usage_mem": "7",
      "gpu_usage_sm": "34",
      "gpu_name": "Tesla T4",
      "gpu_bus_id": "00000000:AF:00.0",
      "gpu_mem": "1227", #mbytes
      "cpu_usage": "470"
    }
  ],
  "updated_at": "2020-10-28 16:50:34"
}
```

**500 - Internal error***

Example:

```javascript
    {'error': 'Undefined exception'}
```


### GET /api/logs/<container_name>/

Get logs filenames


#### Responses:

**200** - GET  http://localhost:8000/api/logs/trusting_diffie/

Example:

```javascript
{
  "manager": [
    {
      "dt": "2020-10-22 15:31:01",
      "filename": "manager_2020_10_22__15_31_01.log"
    },
    {
      "dt": "2020-10-22 13:10:31",
      "filename": "manager_2020_10_22__13_10_31.log"
    }
  ],
  "ffmpeg": [
    {
      "dt": "2020-10-22 15:31:01",
      "filename": "ffmpeg_2020_10_22__15_31_01.log"
    },
    {
      "dt": "2020-10-22 13:10:31",
      "filename": "ffmpeg_2020_10_22__13_10_31.log"
    }
  ]
}
```


**400** - Container name is empty

```javascript
{'error': 'Container name is empty'}
```

**404** - Container's logs dir doesn't exists

```javascript
{'error': "Container logs dir not found"}
```

**500** - Base logs path doesn't exists (/var/log//ffmpeg  by defailt)

```javascript
{'error': "Logs directory doesn't exists <logs path>"}
```



### GET /api/logs/<container_name>/<file_name>/

Returned logs file content in text format


#### Responses

**200** - OK, file content

**400** - container_name is emptyu

```javascript
{'error': 'Container name is empty'}
```

**400** - file_name is emptyu

```javascript
{'error': 'Filename name is empty'}
```

**400** - Wrong filename

```javascript
{'error': 'Wrong file name, must be started with ffmpeg_ or manager_'}
```

**404** - File not found

```javascript
{'error': "File not found"}
```

**500** - Access denied

```javascript
{'error': "Access denied"}
```


### POST /api/ffprobe/

Get info from ffprobe in json. Retunred streams inside 'programs' -> 'streams' and standalone streams in 'streams'

POST Parameter: **addr** - address of stream


#### Responses

**200** - OK

```javascript
{
  "programs": [
    {
      "program_id": 1,
      "program_num": 1,
      "nb_streams": 3,
      "pmt_pid": 101,
      "pcr_pid": 256,
      "start_pts": 1248172,
      "start_time": "8128323.1231",
      "tags": {
        "service_name": "Spas",
        "service_provider": "Spas"
      },
      "streams": [
        {
          "index": 0,
          "codec_name": "h264",
          "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
          "profile": "High",
          "codec_type": "video",
          "codec_time_base": "1/100",
          "codec_tag_string": "[27][0][0][0]",
          "codec_tag": "0x001b",
          "width": 1920,
          "height": 1080,
          "coded_width": 1920,
          "coded_height": 1088,
          "closed_captions": 0,
          "has_b_frames": 1,
          "sample_aspect_ratio": "1:1",
          "display_aspect_ratio": "16:9",
          "pix_fmt": "yuv420p",
          "level": 42,
          "color_range": "tv",
          "color_space": "bt709",
          "color_transfer": "bt709",
          "color_primaries": "bt709",
          "chroma_location": "left",
          "field_order": "progressive",
          "refs": 1,
          "is_avc": "false",
          "nal_length_size": "0",
          "id": "0x100",
          "r_frame_rate": "50/1",
          "avg_frame_rate": "50/1",
          "time_base": "1/90000",
          "start_pts": 1248172,
          "start_time": "305298128323.",
          "bits_per_raw_sample": "8",
          "disposition": {
            "default": 0,
            "dub": 0,
            "original": 0,
            "comment": 0,
            "lyrics": 0,
            "karaoke": 0,
            "forced": 0,
            "hearing_impaired": 0,
            "visual_impaired": 0,
            "clean_effects": 0,
            "attached_pic": 0,
            "timed_thumbnails": 0
          }
        },
        {
          "index": 1,
          "codec_name": "dvb_teletext",
          "codec_long_name": "DVB teletext",
          "codec_type": "subtitle",
          "codec_tag_string": "[6][0][0][0]",
          "codec_tag": "0x0006",
          "id": "0x104",
          "r_frame_rate": "0/0",
          "avg_frame_rate": "0/0",
          "time_base": "1/90000",
          "start_pts": 1248172,
          "start_time": "305298128323.",
          "disposition": {
            "default": 0,
            "dub": 0,
            "original": 0,
            "comment": 0,
            "lyrics": 0,
            "karaoke": 0,
            "forced": 0,
            "hearing_impaired": 0,
            "visual_impaired": 0,
            "clean_effects": 0,
            "attached_pic": 0,
            "timed_thumbnails": 0
          },
          "tags": {
            "language": "rus"
          }
        },
        {
          "index": 2,
          "codec_name": "mp2",
          "codec_long_name": "MP2 (MPEG audio layer 2)",
          "codec_type": "audio",
          "codec_time_base": "1/48000",
          "codec_tag_string": "[3][0][0][0]",
          "codec_tag": "0x0003",
          "sample_fmt": "fltp",
          "sample_rate": "48000",
          "channels": 2,
          "channel_layout": "stereo",
          "bits_per_sample": 0,
          "id": "0x101",
          "r_frame_rate": "0/0",
          "avg_frame_rate": "0/0",
          "time_base": "1/90000",
          "start_pts": 1248172,
          "start_time": "305298128323.",
          "bit_rate": "192000",
          "disposition": {
            "default": 0,
            "dub": 0,
            "original": 0,
            "comment": 0,
            "lyrics": 0,
            "karaoke": 0,
            "forced": 0,
            "hearing_impaired": 0,
            "visual_impaired": 0,
            "clean_effects": 0,
            "attached_pic": 0,
            "timed_thumbnails": 0
          },
          "tags": {
            "language": "rus"
          }
        }
      ]
    }
  ],
  "streams": [
    {
      "index": 3,
      "codec_name": "epg",
      "codec_long_name": "Electronic Program Guide",
      "codec_type": "data",
      "codec_tag_string": "[0][0][0][0]",
      "codec_tag": "0x0000",
      "id": "0x12",
      "r_frame_rate": "0/0",
      "avg_frame_rate": "0/0",
      "time_base": "1/90000",
      "disposition": {
        "default": 0,
        "dub": 0,
        "original": 0,
        "comment": 0,
        "lyrics": 0,
        "karaoke": 0,
        "forced": 0,
        "hearing_impaired": 0,
        "visual_impaired": 0,
        "clean_effects": 0,
        "attached_pic": 0,
        "timed_thumbnails": 0
      }
    }
  ]
}
```

**500** - Returned if exit_code ffprobe != 1

```javascript
{'error': 'Some error'}
```

### POST /api/ffprobe/compile

:parameter template - ff_presets stream template as json (with video and audio template inside as dicts)

**200** - Returned json '{"cmd": "...ffmpeg cmd"}

**400** - "template" parameter not in request. Not valid json or errors in template. Returned json '{"errors": ['error', 'error']}'
