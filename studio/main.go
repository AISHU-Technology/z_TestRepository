package main

import (
	"github.com/gin-gonic/gin"
	_ "kw-studio/docs"
	"kw-studio/global"
	"kw-studio/initialize"
	"kw-studio/upgrade"
	"kw-studio/webui"
)

//go:generate go env -w GO111MODULE=on
//go:generate go env -w GOPROXY=https://goproxy.cn,direct
//go:generate go mod tidy
//go:generate go mod download

func main() {
	//1.初始化配置文件和日志
	global.Config = initialize.Config("./config.yaml", "/etc/studio/kwconfig.yaml")
	global.LOG = initialize.Zap()
	//2.初始化redis客户端
	global.Redis = initialize.Redis()
	//3.初始化gorm
	global.DB = initialize.DB()
	//4.升级
	upgrade.Upgrade()
	//5.初始化路由
	router := initialize.Router()
	webui.AddRoutes(router)

	switch global.Config.Server.Mode {
	case "debug":
		gin.SetMode(gin.DebugMode)
	case "release":
		gin.SetMode(gin.ReleaseMode)
	case "test":
		gin.SetMode(gin.TestMode)
	}
	router.Run(global.Config.Server.Host + ":" + global.Config.Server.Port)
}
