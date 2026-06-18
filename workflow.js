/**
 * 自动化项目生成工作流
 * 端到端执行愿望单中的所有任务
 */

export const meta = {
  name: 'auto-project-generator',
  description: '自动化生成学习型项目，遍历愿望单中的所有任务',
  phases: [
    { title: '解析愿望单', detail: '从 WISHLIST.md 提取所有任务' },
    { title: '并行生成', detail: '同时启动多个子代理实现项目' },
    { title: '验证与记录', detail: '验证结果并记录日志' },
    { title: '迭代处理', detail: '准备下一轮重新调研' }
  ]
}

// 配置
const CONFIG = {
  maxRounds: 2,
  maxConcurrency: 3,  // 最大并行任务数
  retryOnFailure: false,
  logLevel: 'standard'  // 'simple', 'standard', 'detailed'
}

/**
 * 主工作流函数
 */
async function main(args) {
  const { round = 1 } = args || {}

  log(`🚀 启动自动化项目生成器 - 第 ${round} 轮`)
  log(`📁 工作目录: ${process.cwd()}`)

  // Phase 1: 解析愿望单
  phase('解析愿望单')
  const wishes = await parseWishlist()
  log(`📋 解析到 ${wishes.length} 个任务`)

  if (wishes.length === 0) {
    log('⚠️ 愿望单为空，跳过本轮')
    return { success: true, round, completed: 0, failed: 0 }
  }

  // 按优先级排序
  wishes.sort((a, b) => {
    const priorityOrder = { 'P0': 0, 'P1': 1, 'P2': 2 }
    return (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2)
  })

  log(`📊 任务优先级分布:`)
  const priorityCount = {}
  wishes.forEach(w => {
    priorityCount[w.priority] = (priorityCount[w.priority] || 0) + 1
  })
  Object.entries(priorityCount).forEach(([p, c]) => {
    log(`  ${p}: ${c} 个任务`)
  })

  // Phase 2: 并行生成
  phase('并行生成项目')

  // 将任务分组，控制并发
  const batches = []
  for (let i = 0; i < wishes.length; i += CONFIG.maxConcurrency) {
    batches.push(wishes.slice(i, i + CONFIG.maxConcurrency))
  }

  log(`📦 分成 ${batches.length} 批执行，每批最多 ${CONFIG.maxConcurrency} 个任务`)

  const results = []
  let completed = 0
  let failed = 0

  for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
    const batch = batches[batchIndex]
    log(`\n🔄 执行第 ${batchIndex + 1}/${batches.length} 批`)

    // 并行执行当前批次
    const batchResults = await parallel(
      batch.map((wish, index) => () => {
        const taskNum = batchIndex * CONFIG.maxConcurrency + index + 1
        log(`  [${taskNum}/${wishes.length}] 🎯 开始: ${wish.name}`)
        return generateProject(wish, taskNum, wishes.length)
      })
    )

    // 统计结果
    batchResults.forEach((result, index) => {
      const wish = batch[index]
      if (result && result.success) {
        completed++
        wish.status = 'completed'
        log(`  ✅ 完成: ${wish.name}`)
      } else {
        failed++
        wish.status = 'failed'
        wish.error = result?.error || '未知错误'
        log(`  ❌ 失败: ${wish.name} - ${wish.error}`)
      }
      results.push({ wish: wish.name, ...result })
    })
  }

  // Phase 3: 验证与记录
  phase('验证与记录')

  // 保存执行日志
  await saveExecutionLog(round, wishes, results)

  // 生成统计报告
  const stats = {
    round,
    total: wishes.length,
    completed,
    failed,
    successRate: ((completed / wishes.length) * 100).toFixed(1) + '%'
  }

  log(`\n📊 第 ${round} 轮统计:`)
  log(`  成功: ${completed}`)
  log(`  失败: ${failed}`)
  log(`  成功率: ${stats.successRate}`)

  // Phase 4: 迭代处理
  phase('迭代处理')

  if (round < CONFIG.maxRounds) {
    log(`\n⏳ 准备第 ${round + 1} 轮...`)
    log(`  提示: 下一轮将重新调研，抛弃旧选型`)

    // 递归调用，开始下一轮
    const nextResult = await workflow('auto-project-generator', {
      round: round + 1
    })

    return {
      success: true,
      rounds: [stats, nextResult.stats],
      finalCompleted: completed + (nextResult.completed || 0),
      finalFailed: failed + (nextResult.failed || 0)
    }
  }

  log(`\n🎉 所有轮次完成!`)

  return {
    success: true,
    stats,
    completed,
    failed
  }
}

/**
 * 解析愿望单
 */
async function parseWishlist() {
  const content = await readFile('WISHLIST.md')
  if (!content) {
    log('❌ 无法读取 WISHLIST.md')
    return []
  }

  const wishes = []
  const blocks = content.split('\n---\n')

  for (const block of blocks) {
    if (!block.includes('### [')) continue

    const wish = parseWishBlock(block)
    if (wish) {
      wishes.push(wish)
    }
  }

  return wishes
}

/**
 * 解析单个愿望块
 */
function parseWishBlock(block) {
  try {
    // 提取名称
    const nameMatch = block.match(/### \[(.+?)\]/)
    if (!nameMatch) return null
    const name = nameMatch[1]

    // 提取一句话描述
    const descMatch = block.match(/\*\*一句话描述\*\*：(.+)/)
    const description = descMatch ? descMatch[1].trim() : ''

    // 提取学习目标
    const goals = []
    const goalsSection = block.match(/\*\*学习目标\*\*：([\s\S]*?)(?=\*\*|$)/)
    if (goalsSection) {
      goalsSection[1].split('\n').forEach(line => {
        if (line.trim().startsWith('-')) {
          goals.push(line.trim().replace(/^-\s*(目标\d+：)?/, ''))
        }
      })
    }

    // 提取技术栈
    const techStack = {}
    const techSection = block.match(/\*\*技术栈\*\*：([\s\S]*?)(?=\*\*|$)/)
    if (techSection) {
      techSection[1].split('\n').forEach(line => {
        if (line.includes('：')) {
          const [key, value] = line.split('：', 2)
          techStack[key.trim().replace(/^-\s*/, '')] = value.trim()
        }
      })
    }

    // 提取核心循环
    const loopMatch = block.match(/\*\*核心循环\*\*：\s*\n```\n([\s\S]*?)\n```/)
    const coreLoop = loopMatch ? loopMatch[1].trim() : ''

    // 提取参考项目
    const references = []
    const refSection = block.match(/\*\*参考项目\*\*：([\s\S]*?)(?=\*\*|$)/)
    if (refSection) {
      refSection[1].split('\n').forEach(line => {
        if (line.trim().startsWith('-')) {
          references.push(line.trim())
        }
      })
    }

    // 提取优先级
    const priorityMatch = block.match(/\*\*优先级\*\*：(P\d)/)
    const priority = priorityMatch ? priorityMatch[1] : 'P2'

    // 提取预估时长
    const timeMatch = block.match(/\*\*预估时长\*\*：(.+)/)
    const estimatedTime = timeMatch ? timeMatch[1].trim() : ''

    return {
      name,
      description,
      learningGoals: goals,
      techStack,
      coreLoop,
      references,
      priority,
      estimatedTime,
      status: 'pending'
    }
  } catch (error) {
    log(`⚠️ 解析愿望块失败: ${error.message}`)
    return null
  }
}

/**
 * 生成单个项目
 */
async function generateProject(wish, taskNum, totalTasks) {
  const startTime = Date.now()

  try {
    // 创建项目目录
    const projectDir = `projects/${toKebabCase(wish.name)}`

    // 调用子代理实现项目
    const result = await agent(
      `你是一个学习型项目的实现者。请实现以下项目:

项目名称: ${wish.name}
项目描述: ${wish.description}
学习目标: ${wish.learningGoals.join(', ')}
技术栈: ${JSON.stringify(wish.techStack)}
核心循环: ${wish.coreLoop}

要求:
1. 创建完整的项目结构在 ${projectDir} 目录
2. 包含所有必须的文档: README.md, 01-RESEARCH.md, 02-REQUIREMENTS.md, 03-DESIGN.md, 04-PRODUCT.md, 05-DEVELOPMENT.md
3. 实现核心功能代码
4. 编写单元测试
5. 创建使用示例
6. 确保项目可以运行

请按照以下步骤:
1. 先进行市场调研
2. 设计项目架构
3. 实现核心功能
4. 编写测试
5. 创建文档
6. 验证项目可运行

输出格式: JSON { success: boolean, message: string, files: string[] }`,
      {
        label: `generate:${wish.name}`,
        phase: '并行生成',
        schema: {
          type: 'object',
          properties: {
            success: { type: 'boolean' },
            message: { type: 'string' },
            files: { type: 'array', items: { type: 'string' } }
          },
          required: ['success', 'message']
        }
      }
    )

    const duration = ((Date.now() - startTime) / 1000).toFixed(1)

    if (result && result.success) {
      return {
        success: true,
        message: result.message,
        files: result.files || [],
        duration: `${duration}s`
      }
    } else {
      return {
        success: false,
        error: result?.message || '子代理返回失败',
        duration: `${duration}s`
      }
    }
  } catch (error) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(1)
    return {
      success: false,
      error: error.message,
      duration: `${duration}s`
    }
  }
}

/**
 * 保存执行日志
 */
async function saveExecutionLog(round, wishes, results) {
  const log = {
    round,
    timestamp: new Date().toISOString(),
    tasks: wishes.map((wish, index) => ({
      name: wish.name,
      priority: wish.priority,
      status: wish.status,
      error: wish.error || null,
      result: results[index] || null
    }))
  }

  await writeFile(`round_${round}_log.json`, JSON.stringify(log, null, 2))
  log(`💾 执行日志已保存: round_${round}_log.json`)
}

/**
 * 转换为 kebab-case
 */
function toKebabCase(name) {
  return name
    .replace(/[^\w\s-]/g, '')
    .replace(/[-\s]+/g, '-')
    .toLowerCase()
    .trim()
}

// 导出主函数
export default main
