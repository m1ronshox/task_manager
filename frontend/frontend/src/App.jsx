 
import { useEffect, useState } from "react";
import {
  getTasks,
  createTask,
  updateTask,
  deleteTask,
} from "./api";

import {
  Plus,
  Trash2,
  CheckCircle2,
  Circle,
  ListTodo,
} from "lucide-react";

import "./App.css";

function taskError(error) {
  return error.response?.status === 401
    ? "Open or reopen Task Manager from Telegram."
    : "Could not sync tasks. Try again.";
}

function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function fetchTasks() {
    return getTasks()
      .then((response) => {
        setTasks(response.data);
        setError("");
      })
      .catch((error) => setError(taskError(error)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    fetchTasks();
  }, []);

  async function handleAddTask(e) {
    e.preventDefault();

    if (!title.trim()) return;

    try {
      await createTask(title.trim());
      setTitle("");
      fetchTasks();
    } catch (error) {
      setError(taskError(error));
    }
  }

  async function handleComplete(task) {
    try {
      await updateTask(task.id, {
        completed: !task.completed,
      });

      fetchTasks();
    } catch (error) {
      setError(taskError(error));
    }
  }

  async function handleDelete(id) {
    try {
      await deleteTask(id);
      fetchTasks();
    } catch (error) {
      setError(taskError(error));
    }
  }

  const completedCount = tasks.filter(
    (task) => task.completed
  ).length;

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <ListTodo size={28} />
          <h2>Task Manager</h2>
        </div>

        <p>Manage your daily tasks</p>
      </header>

      <main className="container">
        <div className="stats">
          <div>
            <span>Total tasks</span>
            <h2>{tasks.length}</h2>
          </div>

          <div>
            <span>Completed</span>
            <h2>{completedCount}</h2>
          </div>

          <div>
            <span>Remaining</span>
            <h2>{tasks.length - completedCount}</h2>
          </div>
        </div>

        <form className="task-form" onSubmit={handleAddTask}>
          <input
            type="text"
            placeholder="Enter a new task..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <button type="submit">
            <Plus size={20} />
            Add
          </button>
        </form>

        <h3 className="section-title">
          My Tasks
        </h3>

        {error && <p role="alert">{error}</p>}

        {loading ? (
          <p>Loading tasks...</p>
        ) : tasks.length === 0 ? (
          !error && <p className="empty">No tasks yet. Add your first task!</p>
        ) : (
          <div className="task-list">
            {tasks.map((task) => (
              <div className="task-item" key={task.id}>
                <button
                  className="complete-btn"
                  onClick={() => handleComplete(task)}
                >
                  {task.completed ? (
                    <CheckCircle2 color="#16a34a" />
                  ) : (
                    <Circle color="#64748b" />
                  )}
                </button>

                <span
                  className={
                    task.completed ? "completed" : ""
                  }
                >
                  {task.title}
                </span>

                <button
                  className="delete-btn"
                  onClick={() => handleDelete(task.id)}
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
