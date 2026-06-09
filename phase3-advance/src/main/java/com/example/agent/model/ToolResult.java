package com.example.agent.model;

/**
 * 工具调用结果数据模型（来自 D4 清洗数据）
 */
public class ToolResult {
    private String trace_id;
    private String tool;
    private String status;
    private String output;
    private int latency_ms;

    public ToolResult() {
    }

    public ToolResult(String trace_id, String tool, String status, String output, int latency_ms) {
        this.trace_id = trace_id;
        this.tool = tool;
        this.status = status;
        this.output = output;
        this.latency_ms = latency_ms;
    }

    public String getTrace_id() {
        return trace_id;
    }

    public void setTrace_id(String trace_id) {
        this.trace_id = trace_id;
    }

    public String getTool() {
        return tool;
    }

    public void setTool(String tool) {
        this.tool = tool;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getOutput() {
        return output;
    }

    public void setOutput(String output) {
        this.output = output;
    }

    public int getLatency_ms() {
        return latency_ms;
    }

    public void setLatency_ms(int latency_ms) {
        this.latency_ms = latency_ms;
    }
}
