"use client";

import { useState, useEffect } from "react";
import WalletConnect from "@/components/WalletConnect";
import { useVoting } from "@/hooks/useVoting";
import { VoteSession, VoteStatus } from "@/lib/contracts";

export default function Home() {
  const {
    isConnected,
    isLoading,
    error,
    createVoteSession,
    addProposal,
    startVoting,
    vote,
    endVoting,
    getVoteSession,
    getVoteSessionCount,
    account,
  } = useVoting();

  const [sessions, setSessions] = useState<VoteSession[]>([]);
  const [newSession, setNewSession] = useState({
    title: "",
    description: "",
    startTime: "",
    endTime: "",
  });
  const [newProposal, setNewProposal] = useState({
    sessionId: 0,
    name: "",
    description: "",
  });
  const [selectedSession, setSelectedSession] = useState<number | null>(null);

  // 加载投票活动
  useEffect(() => {
    const loadSessions = async () => {
      if (!isConnected) return;

      const count = await getVoteSessionCount();
      const loadedSessions: VoteSession[] = [];

      for (let i = 0; i < count; i++) {
        const session = await getVoteSession(i);
        if (session) {
          loadedSessions.push(session);
        }
      }

      setSessions(loadedSessions);
    };

    loadSessions();
  }, [isConnected, getVoteSessionCount, getVoteSession]);

  // 创建投票活动
  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isConnected) {
      alert("请先连接钱包");
      return;
    }

    try {
      const startTime = Math.floor(new Date(newSession.startTime).getTime() / 1000);
      const endTime = Math.floor(new Date(newSession.endTime).getTime() / 1000);

      await createVoteSession(
        newSession.title,
        newSession.description,
        startTime,
        endTime
      );

      // 重新加载投票活动
      const count = await getVoteSessionCount();
      const session = await getVoteSession(count - 1);
      if (session) {
        setSessions([...sessions, session]);
      }

      setNewSession({ title: "", description: "", startTime: "", endTime: "" });
    } catch (err) {
      console.error("创建投票活动失败:", err);
    }
  };

  // 添加提案
  const handleAddProposal = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isConnected) {
      alert("请先连接钱包");
      return;
    }

    try {
      await addProposal(
        newProposal.sessionId,
        newProposal.name,
        newProposal.description
      );

      // 重新加载投票活动
      const session = await getVoteSession(newProposal.sessionId);
      if (session) {
        setSessions(
          sessions.map((s) => (s.id === session.id ? session : s))
        );
      }

      setNewProposal({ sessionId: 0, name: "", description: "" });
    } catch (err) {
      console.error("添加提案失败:", err);
    }
  };

  // 开始投票
  const handleStartVoting = async (sessionId: number) => {
    try {
      await startVoting(sessionId);

      // 重新加载投票活动
      const session = await getVoteSession(sessionId);
      if (session) {
        setSessions(
          sessions.map((s) => (s.id === session.id ? session : s))
        );
      }
    } catch (err) {
      console.error("开始投票失败:", err);
    }
  };

  // 进行投票
  const handleVote = async (sessionId: number, proposalIndex: number) => {
    try {
      await vote(sessionId, proposalIndex);

      // 重新加载投票活动
      const session = await getVoteSession(sessionId);
      if (session) {
        setSessions(
          sessions.map((s) => (s.id === session.id ? session : s))
        );
      }
    } catch (err) {
      console.error("投票失败:", err);
    }
  };

  // 结束投票
  const handleEndVoting = async (sessionId: number) => {
    try {
      await endVoting(sessionId);

      // 重新加载投票活动
      const session = await getVoteSession(sessionId);
      if (session) {
        setSessions(
          sessions.map((s) => (s.id === session.id ? session : s))
        );
      }
    } catch (err) {
      console.error("结束投票失败:", err);
    }
  };

  // 格式化时间
  const formatTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString("zh-CN");
  };

  // 获取状态文本
  const getStatusText = (status: VoteStatus) => {
    switch (status) {
      case VoteStatus.NotStarted:
        return "未开始";
      case VoteStatus.Active:
        return "进行中";
      case VoteStatus.Ended:
        return "已结束";
      default:
        return "未知";
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: VoteStatus) => {
    switch (status) {
      case VoteStatus.NotStarted:
        return "bg-yellow-100 text-yellow-800";
      case VoteStatus.Active:
        return "bg-green-100 text-green-800";
      case VoteStatus.Ended:
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">去中心化投票系统</h1>
          <WalletConnect />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {!isConnected ? (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold text-gray-700 mb-4">
              欢迎使用去中心化投票系统
            </h2>
            <p className="text-gray-500">请先连接钱包以开始使用</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 左侧：创建投票 */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-lg font-semibold mb-4">创建投票活动</h2>
                <form onSubmit={handleCreateSession} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      投票标题
                    </label>
                    <input
                      type="text"
                      value={newSession.title}
                      onChange={(e) =>
                        setNewSession({ ...newSession, title: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      投票描述
                    </label>
                    <textarea
                      value={newSession.description}
                      onChange={(e) =>
                        setNewSession({
                          ...newSession,
                          description: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      开始时间
                    </label>
                    <input
                      type="datetime-local"
                      value={newSession.startTime}
                      onChange={(e) =>
                        setNewSession({
                          ...newSession,
                          startTime: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      结束时间
                    </label>
                    <input
                      type="datetime-local"
                      value={newSession.endTime}
                      onChange={(e) =>
                        setNewSession({
                          ...newSession,
                          endTime: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? "创建中..." : "创建投票"}
                  </button>
                </form>
              </div>

              {/* 添加提案 */}
              <div className="bg-white rounded-lg shadow-md p-6 mt-6">
                <h2 className="text-lg font-semibold mb-4">添加提案</h2>
                <form onSubmit={handleAddProposal} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      选择投票活动
                    </label>
                    <select
                      value={newProposal.sessionId}
                      onChange={(e) =>
                        setNewProposal({
                          ...newProposal,
                          sessionId: parseInt(e.target.value),
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {sessions.map((session) => (
                        <option key={session.id} value={session.id}>
                          {session.title}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      提案名称
                    </label>
                    <input
                      type="text"
                      value={newProposal.name}
                      onChange={(e) =>
                        setNewProposal({ ...newProposal, name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      提案描述
                    </label>
                    <textarea
                      value={newProposal.description}
                      onChange={(e) =>
                        setNewProposal({
                          ...newProposal,
                          description: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? "添加中..." : "添加提案"}
                  </button>
                </form>
              </div>
            </div>

            {/* 右侧：投票活动列表 */}
            <div className="lg:col-span-2">
              <h2 className="text-lg font-semibold mb-4">投票活动列表</h2>
              {sessions.length === 0 ? (
                <div className="bg-white rounded-lg shadow-md p-6 text-center text-gray-500">
                  暂无投票活动
                </div>
              ) : (
                <div className="space-y-4">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className="bg-white rounded-lg shadow-md p-6"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-xl font-semibold text-gray-900">
                            {session.title}
                          </h3>
                          <p className="text-gray-600 mt-1">
                            {session.description}
                          </p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                            session.status
                          )}`}
                        >
                          {getStatusText(session.status)}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4 text-sm text-gray-500">
                        <div>
                          <span className="font-medium">开始时间：</span>
                          {formatTime(session.startTime)}
                        </div>
                        <div>
                          <span className="font-medium">结束时间：</span>
                          {formatTime(session.endTime)}
                        </div>
                        <div>
                          <span className="font-medium">创建者：</span>
                          {session.creator.slice(0, 6)}...
                          {session.creator.slice(-4)}
                        </div>
                        <div>
                          <span className="font-medium">总投票数：</span>
                          {session.totalVotes}
                        </div>
                      </div>

                      {/* 提案列表 */}
                      {session.proposals.length > 0 && (
                        <div className="mb-4">
                          <h4 className="font-medium text-gray-700 mb-2">
                            提案列表：
                          </h4>
                          <div className="space-y-2">
                            {session.proposals.map((proposal, index) => (
                              <div
                                key={index}
                                className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                              >
                                <div>
                                  <p className="font-medium text-gray-800">
                                    {proposal.name}
                                  </p>
                                  <p className="text-sm text-gray-500">
                                    {proposal.description}
                                  </p>
                                </div>
                                <div className="flex items-center gap-4">
                                  <span className="text-lg font-semibold text-blue-600">
                                    {proposal.voteCount} 票
                                  </span>
                                  {session.status === VoteStatus.Active && (
                                    <button
                                      onClick={() =>
                                        handleVote(session.id, index)
                                      }
                                      disabled={isLoading}
                                      className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                    >
                                      投票
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 操作按钮 */}
                      <div className="flex gap-2">
                        {session.status === VoteStatus.NotStarted &&
                          session.creator.toLowerCase() === account.toLowerCase() && (
                            <button
                              onClick={() => handleStartVoting(session.id)}
                              disabled={isLoading}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                            >
                              开始投票
                            </button>
                          )}
                        {session.status === VoteStatus.Active &&
                          session.creator.toLowerCase() === account.toLowerCase() && (
                            <button
                              onClick={() => handleEndVoting(session.id)}
                              disabled={isLoading}
                              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
                            >
                              结束投票
                            </button>
                          )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
