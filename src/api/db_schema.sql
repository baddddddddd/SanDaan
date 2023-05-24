CREATE TABLE `ping` (
	`count` int NOT NULL AUTO_INCREMENT,
	PRIMARY KEY (`count`)
);

CREATE TABLE `regions` (
	`id` int NOT NULL AUTO_INCREMENT,
	`name` varchar(255),
	PRIMARY KEY (`id`)
);

CREATE TABLE `route_areas` (
	`region_id` int,
	`state_id` int,
	`city_id` int,
	`route_id` int NOT NULL,
	PRIMARY KEY (`route_id`)
);

CREATE TABLE `routes` (
	`id` int NOT NULL AUTO_INCREMENT,
	`name` varchar(255),
	`description` varchar(255),
	`start_time` time,
	`end_time` time,
	`coords` json,
	`connections` json,
	`uploader_id` int,
	PRIMARY KEY (`id`)
);

CREATE TABLE `states` (
	`id` int NOT NULL AUTO_INCREMENT,
	`name` varchar(255),
	PRIMARY KEY (`id`)
);

CREATE TABLE `users` (
	`user_id` int NOT NULL AUTO_INCREMENT,
	`username` varchar(255),
	`email` varchar(255),
	`password` varchar(255),
	PRIMARY KEY (`user_id`)
);
