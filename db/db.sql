CREATE TABLE public.users (
	id serial PRIMARY KEY,
	user_name varchar(30) NOT NULL
);


CREATE TABLE public.querries (
	id serial PRIMARY KEY,
	usr_id int NOT NULL,
	vacancy_search_text varchar(255) NOT NULL,
	countries_id_on_site varchar(255) NOT NULL,
	countries_id_remote varchar(255) NULL,
	remote_words text NULL,
	exclude_by_words text NULL,
	expirience varchar(255) NULL
);
