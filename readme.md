
#requirements
* Python  3.9

#installation
packages:
* numpy
* pandas
* matplotlib
* typing
* fastapi
* python-multipart
  server:
* uvicorn


# config
```cp .env.default .env```

# develop

start server:
```uvicorn main:app --reload```

## generated api docs : 
http://127.0.0.1:8000/docs#/

# routes

## chart 
```
POST http://127.0.0.1:8000/chart
Accept: application/json
Content-Type: application/json

{
  "project": "project-id",
  "step" : "currentstep",
  "type": "mrchart",
  "description": "string",
  "config": {
    "title": "chart.config.title",
    "labelx" : "chart.config.labelx",
    "labely" : "chart.config.labely"
  },
  "data": [
    [27,31,83,14,15,46,17,48,59,10],
    [34,12,64,72,11,23,43,28,41,55]
  ]
}
```

## status
GET http://127.0.0.1:8000/status
