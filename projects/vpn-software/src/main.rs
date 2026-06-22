//! VPN Software - Main entry point
//!
//! A VPN software implementation with tunnel encryption and traffic forwarding.

use std::net::SocketAddr;

use anyhow::Result;
use clap::Parser;
use tracing_subscriber::EnvFilter;

mod cli;
mod config;

use cli::{Cli, Commands};
use config::VpnConfig;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .init();

    // Parse command line arguments
    let cli = Cli::parse();

    // Load configuration
    let config = match &cli.config {
        Some(path) => VpnConfig::load_from_file(path)?,
        None => VpnConfig::default(),
    };

    // Execute command
    match cli.command {
        Commands::Server { port, tun_name, tun_addr } => {
            run_server(config, port, tun_name, tun_addr).await
        }
        Commands::Client { server, port, tun_name, tun_addr } => {
            run_client(config, server, port, tun_name, tun_addr).await
        }
        Commands::GenerateKeys => {
            generate_keys()
        }
        Commands::ShowConfig => {
            show_config(&config)
        }
    }
}

/// Run as VPN server
async fn run_server(
    mut config: VpnConfig,
    port: u16,
    tun_name: String,
    tun_addr: String,
) -> Result<()> {
    tracing::info!("Starting VPN server on port {}", port);

    // Update config with CLI arguments
    config.server.port = port;
    config.tun.name = tun_name;
    config.tun.address = tun_addr.parse()?;

    // Create and start tunnel
    let tunnel_config = vpn_software::tunnel::TunnelConfig {
        listen_port: config.server.port,
        tun_config: vpn_software::tun_device::TunConfig {
            name: config.tun.name.clone(),
            address: config.tun.address,
            netmask: config.tun.netmask,
            mtu: config.tun.mtu,
        },
        peer_public_key: None,
        peer_endpoint: None,
    };

    let tunnel = vpn_software::VpnTunnel::new(tunnel_config).await?;
    tunnel.start().await?;

    tracing::info!("VPN server started successfully");
    tracing::info!("Listening on port {}", port);
    tracing::info!("TUN device: {} ({})", config.tun.name, config.tun.address);

    // Wait for shutdown signal
    tokio::signal::ctrl_c().await?;
    tracing::info!("Shutting down...");

    tunnel.stop().await?;

    Ok(())
}

/// Run as VPN client
async fn run_client(
    mut config: VpnConfig,
    server: String,
    port: u16,
    tun_name: String,
    tun_addr: String,
) -> Result<()> {
    tracing::info!("Connecting to VPN server at {}:{}", server, port);

    // Update config with CLI arguments
    config.client.server = server.clone();
    config.client.port = port;
    config.tun.name = tun_name;
    config.tun.address = tun_addr.parse()?;

    // Create and start tunnel
    let tunnel_config = vpn_software::tunnel::TunnelConfig {
        listen_port: 0, // Random port for client
        tun_config: vpn_software::tun_device::TunConfig {
            name: config.tun.name.clone(),
            address: config.tun.address,
            netmask: config.tun.netmask,
            mtu: config.tun.mtu,
        },
        peer_public_key: None, // Would be loaded from config
        peer_endpoint: Some(format!("{}:{}", server, port).parse::<SocketAddr>()?),
    };

    let tunnel = vpn_software::VpnTunnel::new(tunnel_config).await?;
    tunnel.start().await?;

    tracing::info!("Connected to VPN server");
    tracing::info!("TUN device: {} ({})", config.tun.name, config.tun.address);

    // Wait for shutdown signal
    tokio::signal::ctrl_c().await?;
    tracing::info!("Disconnecting...");

    tunnel.stop().await?;

    Ok(())
}

/// Generate a new keypair
fn generate_keys() -> Result<()> {
    use vpn_software::crypto::generate_keypair;

    let (secret, public) = generate_keypair();

    println!("Generated new keypair:");
    println!("Public key: {:?}", public.as_bytes());
    println!("Secret key: [hidden for security]");

    Ok(())
}

/// Show current configuration
fn show_config(config: &VpnConfig) -> Result<()> {
    println!("VPN Configuration:");
    println!("  Server port: {}", config.server.port);
    println!("  TUN device: {}", config.tun.name);
    println!("  TUN address: {}", config.tun.address);
    println!("  TUN netmask: {}", config.tun.netmask);
    println!("  TUN MTU: {}", config.tun.mtu);

    Ok(())
}
