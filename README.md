# item-catalog
FSND - Item Catalog Project


# Set up vagrant environment

* Create a vagrant box and provision with necessary tool chains

```shell
$ vagrant up
```

* Login to the box

```shell
$ vagrant ssh
$ cd /vagrant
```
* Setup Database

```shell
$python setup_database.py
```

* Run the webserver

```shell
$python item_catalog.py runserver -h 0.0.0.0
```

# JSON End Points

* `/catalogs/JSON`
* `/catalogs/<catalog_name>/items/JSON`
* `/catalogs/<catalog_name>/items/<item_name>/JSON`

# Features
- Custom Login
- Facebook Login
- Google Login
- Create/Read/Update/Delete catalogs
- Create/Read/Update/Delete items
- CRUD operations protected by authentication/authorization
- CSRF protected
