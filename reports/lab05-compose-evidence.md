# Lab 05 Compose Evidence

## docker compose ps
NAME                                IMAGE                            COMMAND                  SERVICE         CREATED          STATUS                    PORTS
fit4110-notification-api-lab05      lab-5-thanhvnnnn-api             "sh -c 'uvicorn noti…"   api             55 seconds ago   Up 44 seconds (healthy)   0.0.0.0:8015->8000/tcp, [::]:8015->8000/tcp
fit4110-notification-db-lab05       postgres:15-alpine               "docker-entrypoint.s…"   db              10 hours ago     Up 54 seconds (healthy)   5432/tcp
fit4110-notification-worker-lab05   lab-5-thanhvnnnn-sender-worker   "uvicorn worker_serv…"   sender-worker   55 seconds ago   Up 54 seconds (healthy)   0.0.0.0:9000->9000/tcp, [::]:9000->9000/tcp

## API health
{
    "status":  "ok",
    "service":  "notification",
    "version":  "1.0.0",
    "dependencies":  {
                         "queue":  "ready",
                         "sender":  "ready",
                         "db":  "ready"
                     }
}

## Worker health
{
    "status":  "ok",
    "service":  "notification-sender-worker",
    "version":  "1.0.0"
}

## DB readiness
/var/run/postgresql:5432 - accepting connections


## API logs tail
fit4110-notification-api-lab05  | INFO:     Started server process [7]
fit4110-notification-api-lab05  | INFO:     Waiting for application startup.
fit4110-notification-api-lab05  | INFO:     Application startup complete.
fit4110-notification-api-lab05  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
fit4110-notification-api-lab05  | INFO:     127.0.0.1:33038 - "GET /health HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:58494 - "GET /health HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "GET /health HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "POST /notifications HTTP/1.1" 202 Accepted
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "POST /notifications HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "GET /notifications?limit=10 HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "GET /notifications/NTF-20260625-0001 HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "POST /notifications/NTF-20260625-0001/retry HTTP/1.1" 202 Accepted
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "GET /templates/security_motion_v1 HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "POST /notifications HTTP/1.1" 401 Unauthorized
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "POST /notifications HTTP/1.1" 422 Unprocessable Entity
fit4110-notification-api-lab05  | INFO:     172.20.0.1:53722 - "GET /core-alerts/ALERT-20260617-0001 HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     127.0.0.1:57734 - "GET /health HTTP/1.1" 200 OK
fit4110-notification-api-lab05  | INFO:     172.20.0.1:39154 - "GET /health HTTP/1.1" 200 OK

