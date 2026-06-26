// Package paxos implements the Paxos consensus algorithm.
//
// Paxos is a consensus algorithm designed by Leslie Lamport.
// It solves the problem of reaching consensus in a distributed system
// where processes may fail or messages may be lost.
//
// # Algorithm Overview
//
// Paxos operates in two phases:
//
//  1. Prepare (Promise) Phase: The proposer requests permission to propose
//     by sending a prepare request with a proposal number to acceptors.
//     Acceptors respond with a promise if the proposal number is higher
//     than any they've seen before.
//
//  2. Accept (Accept) Phase: If the proposer receives promises from a
//     majority, it sends an accept request with its value. Acceptors
//     accept the value unless they've received a higher-numbered prepare.
//
//  3. Learn Phase: Once a majority accepts a value, learners learn the
//     decided value.
//
// # Multi-Paxos
//
// Multi-Paxos optimizes Basic Paxos by electing a single leader that
// handles all proposals, reducing message complexity from O(n^2) to O(n)
// per consensus instance.
package paxos
