from __init__ import CONN, CURSOR

class Employee:

    all = {}

    def __init__(self, name, job_title, department_id, id=None):
        self.id = id
        self.name = name
        self.job_title = job_title
        self.department_id = department_id

    def __repr__(self):
        return f"<Employee {self.id}: {self.name}, {self.job_title}, Dept {self.department_id}>"

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if isinstance(name, str) and len(name):
            self._name = name
        else:
            raise ValueError("Name must be a non-empty string")

    @property
    def job_title(self):
        return self._job_title

    @job_title.setter
    def job_title(self, job_title):
        if isinstance(job_title, str) and len(job_title):
            self._job_title = job_title
        else:
            raise ValueError("Job title must be a non-empty string")

    @property
    def department_id(self):
        return self._department_id

    @department_id.setter
    def department_id(self, department_id):
        if isinstance(department_id, int) and CURSOR.execute(
            "SELECT id FROM departments WHERE id = ?", (department_id,)
        ).fetchone():
            self._department_id = department_id
        else:
            raise ValueError("Department ID must reference a department in the database")

    # ──────────────── CRUD methods ────────────────

    @classmethod
    def create_table(cls):
        """Create a new table to persist the attributes of Employee instances"""
        sql = """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                job_title TEXT,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments (id)
            )
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        """Drop the employees table"""
        sql = "DROP TABLE IF EXISTS employees"
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def create(cls, name, job_title, department_id):
        """Initialize a new Employee instance and save the object to the database"""
        employee = cls(name, job_title, department_id)
        employee.save()
        return employee

    
    def save(self):
        """Insert a new row with the name, job_title, department_id values of the current Employee object.
           Update id, set in self.all dictionary."""
        sql = """
            INSERT INTO employees (name, job_title, department_id)
            VALUES (?, ?, ?)
        """
        CURSOR.execute(sql, (self.name, self.job_title, self.department_id))
        CONN.commit()

        self.id = CURSOR.lastrowid
        type(self).all[self.id] = self

    def update(self):
        """Update the table row corresponding to the current Employee instance."""
        sql = """
            UPDATE employees
            SET name = ?, job_title = ?, department_id = ?
            WHERE id = ?
        """
        CURSOR.execute(sql, (self.name, self.job_title, self.department_id, self.id))
        CONN.commit()

    def delete(self):
        """Delete the table row corresponding to the current Employee instance,
           delete the dictionary entry, and reassign id attribute."""
        sql = "DELETE FROM employees WHERE id = ?"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()
        del type(self).all[self.id]
        self.id = None

    # ──────────────── Finder helpers ────────────────

    @classmethod
    def instance_from_db(cls, row):
        """Return an Employee object with attribute values from table row.
           Prevent duplicate entries in class-level dictionary."""
        if row[0] in cls.all:
            emp = cls.all[row[0]]
            emp.name, emp.job_title, emp.department_id = row[1], row[2], row[3]
        else:
            emp = cls(row[1], row[2], row[3])
            emp.id = row[0]
            cls.all[emp.id] = emp
        return emp

    @classmethod
    def get_all(cls):
        """Return list of Employee objects corresponding to all rows in employees table"""
        sql = "SELECT * FROM employees"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]

    @classmethod
    def find_by_id(cls, id):
        """Return Employee object corresponding to table row matching specified id"""
        sql = "SELECT * FROM employees WHERE id = ?"
        row = CURSOR.execute(sql, (id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def find_by_name(cls, name):
        """Return Employee object corresponding to first table row matching specified name"""
        sql = "SELECT * FROM employees WHERE name = ?"
        row = CURSOR.execute(sql, (name,)).fetchone()
        return cls.instance_from_db(row) if row else None

    # ──────────────── Relationships ────────────────

    def department(self):
        """Return the Department instance the employee belongs to"""
        from department import Department
        sql = "SELECT * FROM departments WHERE id = ?"
        row = CURSOR.execute(sql, (self.department_id,)).fetchone()
        return Department.instance_from_db(row) if row else None

    def reviews(self):
        """Return list of reviews associated with current employee"""
        from review import Review
        sql = "SELECT * FROM reviews WHERE employee_id = ?"
        rows = CURSOR.execute(sql, (self.id,)).fetchall()
        return [Review.instance_from_db(row) for row in rows]
