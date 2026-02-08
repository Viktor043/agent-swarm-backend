/**
 * Example Lovable Component - Agent Swarm Dashboard
 *
 * This is what your Lovable-generated code might look like.
 * Use this as a reference for what Lovable should create.
 */

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

// Configure your backend URL here
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Agent {
  agent_id: string;
  role: string;
  status: string;
  current_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  capabilities: string[];
}

interface Task {
  task_id: string;
  status: string;
  message: string;
}

export default function AgentDashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [taskDescription, setTaskDescription] = useState("");
  const [priority, setPriority] = useState("normal");
  const [loading, setLoading] = useState(false);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);

  // Fetch agents status every 5 seconds
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/agents`);
        const data = await response.json();
        setAgents(data.agents || []);
      } catch (error) {
        console.error("Failed to fetch agents:", error);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  // Submit task to agent swarm
  const handleSubmitTask = async () => {
    if (!taskDescription.trim()) {
      toast.error("Please enter a task description");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          description: taskDescription,
          priority: priority,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to submit task");
      }

      const data: Task = await response.json();

      // Add to recent tasks
      setRecentTasks(prev => [data, ...prev].slice(0, 10));

      toast.success("Task submitted to agent swarm!");
      setTaskDescription("");
    } catch (error) {
      toast.error("Failed to submit task");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Get status badge color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "idle":
        return "bg-green-500";
      case "busy":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-4xl font-bold text-white">
            Agent Swarm Control Center
          </h1>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <span className="text-white text-sm">System Online</span>
          </div>
        </div>

        {/* Task Submission Section */}
        <Card className="bg-white/10 backdrop-blur-lg border-white/20">
          <CardHeader>
            <CardTitle className="text-white">Submit Task to Agents</CardTitle>
            <CardDescription className="text-gray-300">
              Describe what you want the agent swarm to accomplish
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
              placeholder="e.g., 'Build a new feature for the watch app that tracks heart rate' or 'Deploy the dashboard to production'"
              className="min-h-[100px] bg-white/5 border-white/20 text-white placeholder:text-gray-400"
            />

            <div className="flex gap-4 items-center">
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="bg-white/5 border border-white/20 text-white rounded-md px-4 py-2"
              >
                <option value="normal">Normal Priority</option>
                <option value="high">High Priority</option>
                <option value="urgent">Urgent</option>
              </select>

              <Button
                onClick={handleSubmitTask}
                disabled={loading}
                className="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
              >
                {loading ? "Submitting..." : "Submit Task"}
              </Button>
            </div>

            {/* Recent Tasks */}
            {recentTasks.length > 0 && (
              <div className="mt-6 space-y-2">
                <h3 className="text-white font-semibold">Recent Tasks</h3>
                {recentTasks.map((task) => (
                  <div
                    key={task.task_id}
                    className="bg-white/5 border border-white/10 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300 text-sm">{task.task_id}</span>
                      <Badge className={getStatusColor(task.status)}>
                        {task.status}
                      </Badge>
                    </div>
                    <p className="text-white text-sm mt-1">{task.message}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Agent Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <Card
              key={agent.agent_id}
              className="bg-white/10 backdrop-blur-lg border-white/20 hover:bg-white/15 transition-all"
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white text-lg">
                    {agent.role}
                  </CardTitle>
                  <Badge className={getStatusColor(agent.status)}>
                    {agent.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-2xl font-bold text-white">
                      {agent.current_tasks}
                    </p>
                    <p className="text-xs text-gray-400">Active</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-green-400">
                      {agent.completed_tasks}
                    </p>
                    <p className="text-xs text-gray-400">Completed</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-red-400">
                      {agent.failed_tasks}
                    </p>
                    <p className="text-xs text-gray-400">Failed</p>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-400 mb-1">Capabilities:</p>
                  <div className="flex flex-wrap gap-1">
                    {agent.capabilities.map((cap) => (
                      <Badge
                        key={cap}
                        variant="outline"
                        className="text-xs border-white/20 text-white"
                      >
                        {cap}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Social Media Quick Post */}
        <Card className="bg-white/10 backdrop-blur-lg border-white/20">
          <CardHeader>
            <CardTitle className="text-white">Quick Social Media Post</CardTitle>
            <CardDescription className="text-gray-300">
              Post a message from your watch to social platforms
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Textarea
                placeholder="What's on your mind?"
                className="bg-white/5 border-white/20 text-white placeholder:text-gray-400"
              />
              <div className="flex gap-2">
                {["twitter", "linkedin", "facebook", "instagram"].map((platform) => (
                  <Button
                    key={platform}
                    onClick={async () => {
                      try {
                        await fetch(`${API_BASE_URL}/api/connectors/post`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            connector: platform,
                            content: "Test post from agent swarm!",
                          }),
                        });
                        toast.success(`Posted to ${platform}!`);
                      } catch (error) {
                        toast.error(`Failed to post to ${platform}`);
                      }
                    }}
                    className="flex-1 capitalize"
                  >
                    {platform}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/**
 * ENVIRONMENT SETUP
 *
 * In your Lovable project, add this to your .env.local file:
 *
 * NEXT_PUBLIC_API_URL=http://localhost:8000
 *
 * Or for production:
 * NEXT_PUBLIC_API_URL=https://your-backend.railway.app
 *
 * Then Lovable will automatically use the correct API endpoint.
 */
