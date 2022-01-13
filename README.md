# Balerin
## Your application will dance with Balerin!

Balerin is a python package startup orchestrator. it can handle loading all
packages of an application at startup time respecting package dependencies.

Loading all application packages at startup time has many benefits:

- Revealing all syntax errors and invalid imports on startup, preventing runtime failure.
- Initializing all required objects at startup, providing better performance at runtime.
- Triggering all first level objects of a module (ex. decorators) without the need to 
  manually trigger them.
- Better code maintainability by letting you distribute the code on their suitable 
  packages and preventing the need for a centralized location for nonsense 
  imports (ex. models, hooks, managers, ...).

## Installing

**Install using pip**:

**`pip install balerin`**

## Usage Example

The sample code below, is just a rapid showcase on how to develop using Pyrin. 
for a real world application, it is best fit to use the concept of dependency injection 
and IoC which Pyrin is built upon.

To be able to create an application based on Pyrin, the only thing that is required to do
is to subclass from pyrin **`Application`** class in your application package. this is 
needed for Pyrin to be able to find out your application path for generating different 
paths and also loading your application packages. there is no difference where to put 
your subclassed **`Application`**, in this example we put it inside the project's main 
package, inside **`__init__.py`**.

```python
```

## Hint

`Balerin` is an albanian word and means dancer.
