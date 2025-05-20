# WOS planning

A manager-focused dashboard for efficient operations in Whiteout Survival.


## Development

### Running the Project

Start the entire stack:

```shell
docker compose up -d
```

### Access your application

* Frontend: http://localhost:8000/svs
* Backend API: http://localhost:8000/api

## Production

Start the stack

```shell
docker compose -f compose.prod.yml up -d
```

## Privacy

This software only collects the username, user ID, alliance, and state, strictly 
to support planning functionality. No other personal information is gathered. 
All data is stored locally using SQLite and is handled in compliance with major data 
privacy regulations, including the General Data Protection Regulation (GDPR) in Europe 
and the California Consumer Privacy Act (CCPA) in the United States.