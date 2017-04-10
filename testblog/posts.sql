drop table if exists posts;
create table posts (
	id integer primary key autoincrement,
	author string not null,
	text string not null,
	title string not null
);
