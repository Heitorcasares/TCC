drop database if exists Librargo;
create database Librargo;
use Librargo;

create table Usuarios (
	IdUsuario int not null primary key,
    Nome varchar(50) not null,
    Sobrenome varchar(150) not null,
    Email varchar(150) not null,
    FotoDePerfil BLOB
);

create table Cursos (
	IdCurso int not null primary key
);

create table Posts (
	IdPost int not null primary key
);

create table Comentarios (
	IdComentario int not null primary key
);

select * from usuarios;