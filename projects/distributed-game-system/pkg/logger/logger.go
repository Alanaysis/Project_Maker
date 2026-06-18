package logger

import (
	"os"

	"github.com/sirupsen/logrus"
)

var log *logrus.Logger

func init() {
	log = logrus.New()
	log.SetOutput(os.Stdout)
	log.SetLevel(logrus.DebugLevel)
	log.SetFormatter(&logrus.TextFormatter{
		FullTimestamp:   true,
		TimestampFormat: "2006-01-02 15:04:05",
	})
}

// SetLevel 设置日志级别
func SetLevel(level string) {
	switch level {
	case "debug":
		log.SetLevel(logrus.DebugLevel)
	case "info":
		log.SetLevel(logrus.InfoLevel)
	case "warn":
		log.SetLevel(logrus.WarnLevel)
	case "error":
		log.SetLevel(logrus.ErrorLevel)
	default:
		log.SetLevel(logrus.InfoLevel)
	}
}

// Debug 调试日志
func Debug(args ...interface{}) {
	log.Debug(args...)
}

// Debugf 格式化调试日志
func Debugf(format string, args ...interface{}) {
	log.Debugf(format, args...)
}

// Info 信息日志
func Info(args ...interface{}) {
	log.Info(args...)
}

// Infof 格式化信息日志
func Infof(format string, args ...interface{}) {
	log.Infof(format, args...)
}

// Warn 警告日志
func Warn(args ...interface{}) {
	log.Warn(args...)
}

// Warnf 格式化警告日志
func Warnf(format string, args ...interface{}) {
	log.Warnf(format, args...)
}

// Error 错误日志
func Error(args ...interface{}) {
	log.Error(args...)
}

// Errorf 格式化错误日志
func Errorf(format string, args ...interface{}) {
	log.Errorf(format, args...)
}

// Fatal 致命错误日志
func Fatal(args ...interface{}) {
	log.Fatal(args...)
}

// Fatalf 格式化致命错误日志
func Fatalf(format string, args ...interface{}) {
	log.Fatalf(format, args...)
}

// WithField 添加字段
func WithField(key string, value interface{}) *logrus.Entry {
	return log.WithField(key, value)
}

// WithFields 添加多个字段
func WithFields(fields logrus.Fields) *logrus.Entry {
	return log.WithFields(fields)
}
