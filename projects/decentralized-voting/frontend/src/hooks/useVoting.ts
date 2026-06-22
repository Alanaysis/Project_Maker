"use client";

import { useState, useEffect, useCallback } from "react";
import { ethers } from "ethers";
import { VOTING_ABI, VOTING_CONTRACT_ADDRESS, VoteStatus, VoteSession, Proposal } from "@/lib/contracts";

export function useVoting() {
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null);
  const [signer, setSigner] = useState<ethers.Signer | null>(null);
  const [contract, setContract] = useState<ethers.Contract | null>(null);
  const [account, setAccount] = useState<string>("");
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  // 连接钱包
  const connectWallet = useCallback(async () => {
    try {
      if (!window.ethereum) {
        throw new Error("请安装 MetaMask 钱包");
      }

      const browserProvider = new ethers.BrowserProvider(window.ethereum);
      const signer = await browserProvider.getSigner();
      const address = await signer.getAddress();

      setProvider(browserProvider);
      setSigner(signer);
      setAccount(address);
      setIsConnected(true);

      // 初始化合约
      if (VOTING_CONTRACT_ADDRESS) {
        const votingContract = new ethers.Contract(
          VOTING_CONTRACT_ADDRESS,
          VOTING_ABI,
          signer
        );
        setContract(votingContract);
      }
    } catch (err: any) {
      setError(err.message || "连接钱包失败");
    }
  }, []);

  // 检查是否已连接
  useEffect(() => {
    const checkConnection = async () => {
      if (window.ethereum) {
        const accounts = await window.ethereum.request({ method: "eth_accounts" });
        if (accounts.length > 0) {
          connectWallet();
        }
      }
    };
    checkConnection();
  }, [connectWallet]);

  // 创建投票活动
  const createVoteSession = useCallback(
    async (title: string, description: string, startTime: number, endTime: number) => {
      if (!contract || !signer) {
        throw new Error("请先连接钱包");
      }

      setIsLoading(true);
      setError("");

      try {
        const tx = await contract.createVoteSession(title, description, startTime, endTime);
        const receipt = await tx.wait();

        // 从事件中获取 sessionId
        const event = receipt.logs.find((log: any) => {
          try {
            const parsed = contract.interface.parseLog(log);
            return parsed?.name === "VoteSessionCreated";
          } catch {
            return false;
          }
        });

        if (event) {
          const parsed = contract.interface.parseLog(event);
          return parsed?.args.sessionId;
        }

        return null;
      } catch (err: any) {
        setError(err.message || "创建投票活动失败");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [contract, signer]
  );

  // 添加提案
  const addProposal = useCallback(
    async (sessionId: number, name: string, description: string) => {
      if (!contract || !signer) {
        throw new Error("请先连接钱包");
      }

      setIsLoading(true);
      setError("");

      try {
        const tx = await contract.addProposal(sessionId, name, description);
        await tx.wait();
      } catch (err: any) {
        setError(err.message || "添加提案失败");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [contract, signer]
  );

  // 开始投票
  const startVoting = useCallback(
    async (sessionId: number) => {
      if (!contract || !signer) {
        throw new Error("请先连接钱包");
      }

      setIsLoading(true);
      setError("");

      try {
        const tx = await contract.startVoting(sessionId);
        await tx.wait();
      } catch (err: any) {
        setError(err.message || "开始投票失败");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [contract, signer]
  );

  // 进行投票
  const vote = useCallback(
    async (sessionId: number, proposalIndex: number) => {
      if (!contract || !signer) {
        throw new Error("请先连接钱包");
      }

      setIsLoading(true);
      setError("");

      try {
        const tx = await contract.vote(sessionId, proposalIndex);
        await tx.wait();
      } catch (err: any) {
        setError(err.message || "投票失败");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [contract, signer]
  );

  // 结束投票
  const endVoting = useCallback(
    async (sessionId: number) => {
      if (!contract || !signer) {
        throw new Error("请先连接钱包");
      }

      setIsLoading(true);
      setError("");

      try {
        const tx = await contract.endVoting(sessionId);
        await tx.wait();
      } catch (err: any) {
        setError(err.message || "结束投票失败");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [contract, signer]
  );

  // 获取投票活动详情
  const getVoteSession = useCallback(
    async (sessionId: number): Promise<VoteSession | null> => {
      if (!contract) {
        return null;
      }

      try {
        const session = await contract.getVoteSession(sessionId);
        const proposalCount = await contract.getProposalCount(sessionId);

        const proposals: Proposal[] = [];
        for (let i = 0; i < proposalCount; i++) {
          const [name, description, voteCount] = await contract.getProposal(sessionId, i);
          proposals.push({
            name,
            description,
            voteCount: Number(voteCount),
          });
        }

        return {
          id: sessionId,
          title: session.title,
          description: session.description,
          creator: session.creator,
          startTime: Number(session.startTime),
          endTime: Number(session.endTime),
          status: Number(session.status) as VoteStatus,
          totalVotes: Number(session.totalVotes),
          proposals,
        };
      } catch (err: any) {
        setError(err.message || "获取投票活动失败");
        return null;
      }
    },
    [contract]
  );

  // 获取投票活动数量
  const getVoteSessionCount = useCallback(async (): Promise<number> => {
    if (!contract) {
      return 0;
    }

    try {
      const count = await contract.voteSessionCount();
      return Number(count);
    } catch (err: any) {
      setError(err.message || "获取投票活动数量失败");
      return 0;
    }
  }, [contract]);

  // 检查用户是否已投票
  const hasVoted = useCallback(
    async (sessionId: number, address: string): Promise<boolean> => {
      if (!contract) {
        return false;
      }

      try {
        return await contract.hasVoted(sessionId, address);
      } catch {
        return false;
      }
    },
    [contract]
  );

  // 获取用户的投票选择
  const getVotedProposal = useCallback(
    async (sessionId: number, address: string): Promise<number> => {
      if (!contract) {
        return -1;
      }

      try {
        const proposalIndex = await contract.getVotedProposal(sessionId, address);
        return Number(proposalIndex);
      } catch {
        return -1;
      }
    },
    [contract]
  );

  return {
    provider,
    signer,
    contract,
    account,
    isConnected,
    isLoading,
    error,
    connectWallet,
    createVoteSession,
    addProposal,
    startVoting,
    vote,
    endVoting,
    getVoteSession,
    getVoteSessionCount,
    hasVoted,
    getVotedProposal,
  };
}
