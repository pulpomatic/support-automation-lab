-- ====================================================
-- CONFIGURACIÓN DE VARIABLES
-- ====================================================
-- Cambia estos valores según sea necesario.
-- En DBeaver puedes definir variables de sustitución usando ${variable}.
-- Ejemplo:
--   account_id  : 291251
--   creator_id  : 6
--
-- Si prefieres, puedes dejar este comentario como referencia
-- y utilizar la función de "Script Parameters" de DBeaver.
-- 
-- 
-- Considera que estas operaciones son directamente en base de datos y no hace trigger de envío de correos ni nada por el estilo.
-- 
-- ====================================================
-- Consultamos la cuenta
-- ====================================================
select *
from accounts
where name ilike '%OHL%';

-- ====================================================
-- Consultamos el usuario (en este caso fue id 6)
-- ====================================================
select u.*
from users u
inner join accounts_users au on au.user_id = u.id 
where au.account_id = ${account_id}
  and u.email ilike '%armando.perdomo@getpulpo.com%';

/*
 * Primero debemos actualizar los notificables en la tabla users_reminders.
 * Se busca el usuario creador del recordatorio (en este ejemplo, id = ${creator_id})
 * y se elimina como notificable.
 */
delete from users_reminders
where reminder_id in (
    select r.id
    from reminders r
    where r.status = 'ACTIVE'
      and r.account_id = ${account_id}
      and r.responsible_id = ${creator_id}
)
  and user_id = ${creator_id};

-- ====================================================
-- Insertamos los usuarios administradores como notificables
-- ====================================================
-- Seleccionamos los usuarios admins
with account_admins as (
    select u.id, u.email
    from users u
    inner join accounts_users au on au.user_id = u.id 
    where au.account_id = ${account_id}
      /* Puedes filtrar por email si lo requieres:
         and u.email in ('armando.perdomo@getpulpo.com')
      */
      and au.user_type_id = 2  -- (en caso de que necesites todos los admins)
)
select *
from account_admins;

/*
 * Ahora insertamos los recordatorios a los admins, si son 2 admins y 10 recordatorios el select dentro del with debe dar 20 registros
 * que es la union de los ids de admins mas los ids de recordatorios
 * */
with reminders_admins as (
    select 
        r.id as reminder_id, 
        u.admin_id as admin_id
    from reminders r
    cross join (
        select u.id as admin_id 
        from users u
        inner join accounts_users au on au.user_id = u.id
        where au.account_id = ${account_id}
          and u.email in (
              'pfraile@ohla-group.com',
              'rpzanca@ohla-group.com'
          )
    ) u
    where r.account_id = ${account_id}
      and r.status = 'ACTIVE'
      and r.created_by_user_id = ${creator_id}
)
insert into users_reminders (user_id, status, account_id, reminder_id)
select admin_id, 'pending', ${account_id}, reminder_id
from reminders_admins;

-- ====================================================
-- Consultamos los recordatorios activos (insertados por la carga del script)
-- La idea es mover todos los recordatorios creados por el usuario creador (${creator_id}) a los administradores.
-- ====================================================
select r.id, r.created_at, *
from reminders r
where r.status = 'ACTIVE'
  and r.account_id = ${account_id}
  and r.responsible_id = ${creator_id}
order by r.created_at desc;

-- ====================================================
-- Actualizamos el responsable en los recordatorios
-- Se asigna el administrador principal (en este caso, ${creator_id})
-- ====================================================
update reminders
set responsible_id = ${admin_id},
    created_by_user_id = ${admin_id}
where id in (
    select r.id
    from reminders r
    where r.status = 'ACTIVE'
      and r.account_id = ${account_id}
      and r.responsible_id = ${creator_id}
);
