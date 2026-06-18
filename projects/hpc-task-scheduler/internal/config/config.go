package config

// Config 系统配置
type Config struct {
	Server    ServerConfig
	Scheduler SchedulerConfig
	Resources ResourceConfig
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Port string
}

// SchedulerConfig 调度器配置
type SchedulerConfig struct {
	// 调度算法: fifo, priority, fair
	Algorithm    string
	// 调度间隔(毫秒)
	IntervalMs   int
	// 最大重试次数
	MaxRetries   int
	// 任务超时(秒)
	TaskTimeout  int
}

// ResourceConfig 资源配置
type ResourceConfig struct {
	// 总 CPU 核数
	TotalCPU     int
	// 总内存(MB)
	TotalMemoryMB int
	// 是否启用 cgroups
	EnableCgroups bool
	// cgroups 路径
	CgroupsPath  string
}

// DefaultConfig 返回默认配置
func DefaultConfig() *Config {
	return &Config{
		Server: ServerConfig{
			Port: "8080",
		},
		Scheduler: SchedulerConfig{
			Algorithm:   "fifo",
			IntervalMs:  1000,
			MaxRetries:  3,
			TaskTimeout: 300,
		},
		Resources: ResourceConfig{
			TotalCPU:      8,
			TotalMemoryMB: 16384,
			EnableCgroups: false,
			CgroupsPath:   "/sys/fs/cgroup",
		},
	}
}
