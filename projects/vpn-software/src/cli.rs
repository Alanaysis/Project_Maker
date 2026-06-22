//! Command line interface for VPN software

use clap::{Parser, Subcommand};

/// VPN Software - A secure tunnel implementation
#[derive(Parser)]
#[command(name = "vpn-software")]
#[command(about = "A VPN software implementation with tunnel encryption")]
#[command(version)]
pub struct Cli {
    /// Configuration file path
    #[arg(short, long)]
    pub config: Option<String>,

    /// Enable verbose logging
    #[arg(short, long)]
    pub verbose: bool,

    #[command(subcommand)]
    pub command: Commands,
}

/// Available commands
#[derive(Subcommand)]
pub enum Commands {
    /// Run as VPN server
    Server {
        /// Listening port
        #[arg(short, long, default_value = "51820")]
        port: u16,

        /// TUN device name
        #[arg(short = 'n', long, default_value = "tun0")]
        tun_name: String,

        /// TUN device address
        #[arg(short = 'a', long, default_value = "10.0.0.1")]
        tun_addr: String,
    },

    /// Run as VPN client
    Client {
        /// Server address
        #[arg(short, long)]
        server: String,

        /// Server port
        #[arg(short, long, default_value = "51820")]
        port: u16,

        /// TUN device name
        #[arg(short = 'n', long, default_value = "tun0")]
        tun_name: String,

        /// TUN device address
        #[arg(short = 'a', long, default_value = "10.0.0.2")]
        tun_addr: String,
    },

    /// Generate a new keypair
    GenerateKeys,

    /// Show current configuration
    ShowConfig,
}
