# Balerin
## Your application will dance with Balerin!

Balerin is a python package startup orchestrator. it can handle loading all
packages of an application at startup time respecting package dependencies.

Loading all application packages at startup has many benefits:

- Revealing all syntax errors and invalid imports on startup, preventing runtime failure.
- Initializing all required objects at startup, providing better performance at runtime.
- Triggering all first level objects of a module (ex. decorators) without the need to 
  manually trigger them.
- Better code maintainability by letting you distribute the code on their suitable 
  packages and preventing the need for a centralized location for nonsense 
  imports (ex. models, hooks, managers, ...).
- Auto registration of celery tasks without the need to name all task modules a 
  specific name (usually tasks).
- Populating application level caches at startup to boost performance at runtime.

## Installing

**Install using pip**:

**`pip install balerin`**

## Usage Example

**There are two ways to use Balerin in your project:**

- *Basic*: Loading all packages based on filesystem order.
  (the order could be changed between each run).
- *Pro*: Loading all packages respecting their dependencies on each other.
  (the order will be always the same on every run).

**Sample Project Structure:**

- root_dir
  - my_app
    - accounting
      - `__init__.py`
      - `api.py`
    - customers
      - `__init__.py`
      - `models.py`
    - `__init__.py`
    - `api.py`
    - `models.py`
  - `start.py`

### Basic Usage:

**`start.py:`**

```python
import os

from flask import Flask
from balerin import PackagingManager


if __name__ == '__main__':
    my_app = Flask()
    working_directory = os.path.abspath(os.getcwd())
    root_package = os.path.join(working_directory, 'my_app')
    balerin = PackagingManager(root_package)
    balerin.load_components()
    # Here the application is loaded, and you can call run() on your app:
    my_app.run()
```

### Pro Usage:

In order to load packages respecting their dependencies on each other, you must define 
a package class in `__init__.py` file of each package that has dependency on other packages.
The package class must be a subclass of Balerin's `Package` class:

**`my_app/accounting/__init__.py:`**

```python
from balerin import Package


class AccountingPackage(Package):
    # the name of the package.
    # example: `my_app.api`.
    # should get it from `__name__` for each package.
    NAME = __name__

    # list of all packages that this package is dependent
    # on them and should be loaded after all of them.
    # example: ['my_app.logging', 'my_app.api.public']
    # this can be left as an empty list if there is no dependencies.
    DEPENDS = ['my_app.customers']

    # specifies that this package is enabled and must be loaded.
    ENABLED = True

    # name of a module inside this package that should be loaded before all other modules.
    # for example: 'manager'
    # this can be left as None if there is no such file in this package needing early loading.
    COMPONENT_NAME = None
```

Now you can load your packages respecting their dependencies on each other, using 
the sample code in **`Basic Usage`** section.

### Initialization Arguments of PackagingManager Class:

- `root`: it can be a single or multiple paths to different packages of your application.
          Balerin will load all sub-packages of each path respectively.
- `base_component`: specifies a module name which must be loaded before all other modules 
                    in each package if available. for example *manager*. this value could be 
                    overridden in each *Package* class using *COMPONENT_NAME* attribute.
- `verbose`: specifies that loading info should be printed on each step.
             defaults to True if not provided.
- `ignored_packages`: list of package names that must be ignored from loading. package names 
                      must be fully qualified. for example: *my_app.accounting.public*. 
                      notice that if a package that has sub-packages added to ignore list, 
                      all of its sub-packages will be ignored automatically even if not 
                      present in ignore list.
- `ignored_modules`: list of module names that must be ignored from loading. 
                     module names could be fully qualified or just the module name itself.
                     for example: *my_app.customers.models* or *models*.
                     notice that if only module name is provided, then all modules matching 
                     the provided name will be ignored from loading.

## How to Choose Between Basic or Pro Usages:

In most cases, you don't need to use the `Pro Usage` style. unless your application 
architecture is based on `Dependency Injection` and `IoC` concepts. so, when in doubt, go 
with `Basic Usage`.

## Hint

`Balerin` is an albanian word and means dancer.
