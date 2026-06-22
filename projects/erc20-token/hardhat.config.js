import hardhatEthers from "@nomicfoundation/hardhat-ethers";
import hardhatMocha from "@nomicfoundation/hardhat-mocha";
import hardhatChaiMatchers from "@nomicfoundation/hardhat-ethers-chai-matchers";
import { defineConfig } from "hardhat/config";

export default defineConfig({
  plugins: [hardhatEthers, hardhatMocha, hardhatChaiMatchers],
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    // The default Hardhat Network is automatically configured as "edr-simulated".
    // Uncomment and fill in to deploy to a testnet:
    // sepolia: {
    //   type: "http",
    //   url: `https://eth-sepolia.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
    //   accounts: [process.env.PRIVATE_KEY],
    // },
  },
});
