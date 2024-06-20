# Processing files fastapi htmx

On upload csv file add it to processing queue and show processing status on SPA index page.
Handling file - emulation hard CPU bound task.

## docs
Swagger on `/docs`.

## Run

```sh
cd /path/to/project/dir/
docker compose up -d
```
Open homepage:
[`http://127.0.0.1:8000/`](http://127.0.0.1:8000/)
<span style="background-color: #e5f5fc; padding: 20px; display: block;">Compose doesn't contains Nginx or ect. If service isn't local change url hostname.</span>

## Run Development

```sh
cd /path/to/project/dir/
docker compose -f docker-compose.dev.yml up -d
```

### Environments

#### .env.db
 - POSTGRES_USER
 - POSTGRES_PASSWORD
 - POSTGRES_DB

#### .env.redis
 - REDIS_PASSWORD
 - REDIS_PORT - standart
 - REDIS_DATABASES


## API schema

### Templates

#### Homepage [GET] `/` SPA Index page.


#### [POST] `/processing_file/` Create ProcessingFile
Content-Type: multipart/from-data

Params:
  - file - with MIME type text/csv

Triggering `/processing_file/listen-updates/` - event.

#### [DELETE] `/processing_file/{file_id: int}/` Cancel or Remove ProcessingFile
Set current file <b>status</b> `'Removed'` when it has <b>status</b> `'Ok'` and remove local data from `./media/`
else set current file <b>status</b> `'Canceled'`.

Triggering `/processing_file/listen-updates/` - event.

Params:
  - file_id - int id

#### [GET] `/processing_file/{file_id: int}/detail/`
Returns popup template detail with info about current ProcessingFile.


### Events

#### [GET] `/processing_file/listen-updates/` event:handlingStatusChanged
Trigger for updating table with list ProcessingFiles on index page.

Format: `"event: handlingStatusChanged\ndata: {content}\n\n"` - where content is table for replace it on index page.

## HTMX

### HTMX Extentions

  - [remove-me](https://github.com/bigskysoftware/htmx-extensions/blob/main/src/remove-me/README.md) - remove block by time trigger.
  - [see](https://github.com/bigskysoftware/htmx-extensions/blob/main/src/sse/README.md) - Server Sent Events.

### [index.html](./templates/index.html)
  - [6] hx-ext "remove-me" - view info messages. Messages deleting by time trigger in seconds.
  - [13] hx-ext "see" - update table on each <b>handlingStatusChanged</b> server event.
### [uploadfile_htmx.html](./templates/forms/uploadfile_htmx.html)
  - [1] hx-post `/processing_file/` - send post request.

### [processing_file/list.html](./templates/processing_files/list.html)
 - [23] hx-delete `/processing_file/{file_id: int}/` - send delete request for current file for cancel operation or clear local file data.
