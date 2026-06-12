package com.yupi.datacleaning.cleaning;

import tech.tablesaw.api.Table;
import tech.tablesaw.api.StringColumn;
import tech.tablesaw.api.DoubleColumn;
import tech.tablesaw.api.IntColumn;
import tech.tablesaw.api.LongColumn;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.DoubleStream;

@Slf4j
@Service
public class DataCleaner {

    // 增强的正则表达式 - 来自知识库
    private static final Pattern PHONE_PATTERN = Pattern.compile("1[3-9]\\d{9}");
    private static final Pattern ID_CARD_18_PATTERN = Pattern.compile("[1-9]\\d{5}(18|19|20)\\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\\d{3}[0-9Xx]");
    private static final Pattern ID_CARD_SIMPLE_PATTERN = Pattern.compile("\\d{17}[\\dXx]");
    private static final Pattern EMAIL_PATTERN = Pattern.compile("\\w+([-+.]\\w+)*@\\w+([-.]\\w+)*\\.\\w+([-.]\\w+)*");
    private static final Pattern IP_PATTERN = Pattern.compile("\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}");
    private static final Pattern BANK_CARD_PATTERN = Pattern.compile("\\d{16,19}");
    // 日期和时间格式模式
    private static final Pattern DATE_ISO_PATTERN = Pattern.compile("\\d{4}-\\d{1,2}-\\d{1,2}");
    private static final Pattern DATE_SLASH_PATTERN = Pattern.compile("(\\d{4})/(\\d{1,2})/(\\d{1,2})");
    private static final Pattern DATE_DASH_PATTERN = Pattern.compile("(\\d{1,2})-(\\d{1,2})-(\\d{4})");
    private static final Pattern DATE_CHINESE_PATTERN = Pattern.compile("(\\d{4})年(\\d{1,2})月(\\d{1,2})日");
    private static final Pattern DATETIME_SLASH_PATTERN = Pattern.compile("(\\d{4})/(\\d{1,2})/(\\d{1,2})[ T]*(\\d{1,2}):(\\d{1,2})(?::(\\d{1,2}))?");
    private static final Pattern DATETIME_ISO_PATTERN = Pattern.compile("(\\d{4})-(\\d{1,2})-(\\d{1,2})[ T]*(\\d{1,2}):(\\d{1,2})(?::(\\d{1,2}))?");
    private static final Pattern DATETIME_ISO_TZ_PATTERN = Pattern.compile("(\\d{4})-(\\d{1,2})-(\\d{1,2})T(\\d{1,2}):(\\d{1,2}):(\\d{1,2})[+-]\\d{2}:\\d{2}");
    private static final Pattern TIMESTAMP_PATTERN = Pattern.compile("\\d{10,13}");
    
    // 文本清洗相关
    private static final Pattern CONTROL_CHARS_PATTERN = Pattern.compile("[\\p{Cntrl}]");
    private static final Pattern MULTIPLE_SPACES_PATTERN = Pattern.compile("\\s+");
    private static final Pattern HTML_TAGS_PATTERN = Pattern.compile("<[^>]*>");
    private static final Pattern EMOJI_PATTERN = Pattern.compile("[\\p{So}]");
    
    // 特殊标记清理 - 从数据中发现的标记
    private static final Pattern SPECIAL_MARK_PATTERN = Pattern.compile(
        "(>>>( \\[draft\\])?|ENDEND|@@@|#todo|cache=false|stdout:|【|】|「|」|\\*\\*|—|—|…|！{2,}|~$|\\(口述\\)|\\[ASR\\])",
        Pattern.CASE_INSENSITIVE
    );
    
    // 错别字修正
    private static final Map<String, String> TYPO_CORRECTIONS = Map.of(
        "知只库", "知识库",
        "其麟", "麒麟"
    );

    // ==================== 1. 缺失值处理 ====================
    
    public Table fillMissingValues(Table table, CleaningReport report) {
        int totalFilled = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof DoubleColumn) {
                // 数值列：计算中位数填充（知识库推荐）
                DoubleColumn column = table.doubleColumn(columnName);
                double median = calculateMedian(column);
                int colFilled = 0;
                
                if (!Double.isNaN(median)) {
                    for (int i = 0; i < column.size(); i++) {
                        if (Double.isNaN(column.getDouble(i))) {
                            column.set(i, median);
                            colFilled++;
                        }
                    }
                    table.replaceColumn(columnName, column);
                }
                
                if (colFilled > 0) {
                    report.addColumnStat(columnName + " (数值-中位数填充)", colFilled);
                    totalFilled += colFilled;
                }
            } else if (table.column(columnName) instanceof StringColumn) {
                // 文本列：用空字符串或"未知"填充
                StringColumn column = table.stringColumn(columnName);
                int colFilled = 0;
                
                for (int i = 0; i < column.size(); i++) {
                    if (column.get(i) == null || column.get(i).trim().isEmpty()) {
                        column.set(i, "");
                        colFilled++;
                    }
                }
                table.replaceColumn(columnName, column);
                
                if (colFilled > 0) {
                    report.addColumnStat(columnName + " (文本-空值填充)", colFilled);
                    totalFilled += colFilled;
                }
            }
        }
        report.setFilledMissingValues(totalFilled);
        log.info("Filled {} missing values using median/empty string strategy", totalFilled);
        return table;
    }
    
    private double calculateMedian(DoubleColumn column) {
        List<Double> nonNullValues = new ArrayList<>();
        for (int i = 0; i < column.size(); i++) {
            double val = column.getDouble(i);
            if (!Double.isNaN(val)) {
                nonNullValues.add(val);
            }
        }
        
        if (nonNullValues.isEmpty()) {
            return Double.NaN;
        }
        
        Collections.sort(nonNullValues);
        int middle = nonNullValues.size() / 2;
        
        if (nonNullValues.size() % 2 == 0) {
            return (nonNullValues.get(middle - 1) + nonNullValues.get(middle)) / 2.0;
        } else {
            return nonNullValues.get(middle);
        }
    }

    // ==================== 2. 重复数据检测 ====================
    
    public Table removeDuplicates(Table table, CleaningReport report) {
        int originalCount = table.rowCount();
        Table result = table.dropDuplicateRows();
        int removed = originalCount - result.rowCount();
        report.setRemovedDuplicates(removed);
        report.setOriginalRowCount(originalCount);
        log.info("Removed {} duplicate rows (全字段匹配)", removed);
        return result;
    }

    // ==================== 3. 异常值检测与处理 ====================
    
    public Table handleOutliers(Table table, CleaningReport report) {
        int totalHandled = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof DoubleColumn) {
                DoubleColumn column = table.doubleColumn(columnName);
                
                // 使用 IQR 方法检测异常值
                double[] bounds = calculateIQRBounds(column);
                double lowerBound = bounds[0];
                double upperBound = bounds[1];
                
                int colHandled = 0;
                for (int i = 0; i < column.size(); i++) {
                    double val = column.getDouble(i);
                    if (!Double.isNaN(val) && (val < lowerBound || val > upperBound)) {
                        // 截断到边界值
                        column.set(i, val < lowerBound ? lowerBound : upperBound);
                        colHandled++;
                    }
                }
                
                if (colHandled > 0) {
                    report.addColumnStat(columnName + " (异常值截断)", colHandled);
                    totalHandled += colHandled;
                    table.replaceColumn(columnName, column);
                }
            }
        }
        log.info("Handled {} outlier values using IQR method", totalHandled);
        report.setHandledOutliers(totalHandled);
        return table;
    }
    
    private double[] calculateIQRBounds(DoubleColumn column) {
        List<Double> nonNullValues = new ArrayList<>();
        for (int i = 0; i < column.size(); i++) {
            double val = column.getDouble(i);
            if (!Double.isNaN(val)) {
                nonNullValues.add(val);
            }
        }
        
        if (nonNullValues.size() < 4) {
            return new double[]{Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY};
        }
        
        Collections.sort(nonNullValues);
        int n = nonNullValues.size();
        
        double q1 = getPercentile(nonNullValues, 25);
        double q3 = getPercentile(nonNullValues, 75);
        double iqr = q3 - q1;
        
        return new double[]{q1 - 1.5 * iqr, q3 + 1.5 * iqr};
    }
    
    private double getPercentile(List<Double> sortedValues, int percentile) {
        int index = (int) Math.ceil(percentile / 100.0 * sortedValues.size()) - 1;
        return sortedValues.get(Math.max(0, Math.min(index, sortedValues.size() - 1)));
    }

    // ==================== 4. 敏感信息脱敏 ====================
    
    public Table maskSensitiveData(Table table, CleaningReport report) {
        int totalMasked = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colMasked = 0;
                
                column = column.map(s -> {
                    if (s == null) return null;
                    String masked = s;
                    boolean modified = false;
                    
                    // 手机号脱敏：保留前3后4，中间星号
                    Matcher phoneMatcher = PHONE_PATTERN.matcher(masked);
                    StringBuffer sb = new StringBuffer();
                    while (phoneMatcher.find()) {
                        String phone = phoneMatcher.group();
                        String maskedPhone = phone.substring(0, 3) + "****" + phone.substring(7);
                        phoneMatcher.appendReplacement(sb, maskedPhone);
                        modified = true;
                    }
                    phoneMatcher.appendTail(sb);
                    masked = sb.toString();
                    
                    // 邮箱脱敏：保留首字符和域名
                    Matcher emailMatcher = EMAIL_PATTERN.matcher(masked);
                    sb = new StringBuffer();
                    while (emailMatcher.find()) {
                        String email = emailMatcher.group();
                        int atIndex = email.indexOf('@');
                        if (atIndex > 1) {
                            String maskedEmail = email.charAt(0) + "***" + email.substring(atIndex);
                            emailMatcher.appendReplacement(sb, maskedEmail);
                            modified = true;
                        }
                    }
                    emailMatcher.appendTail(sb);
                    masked = sb.toString();
                    
                    // 身份证脱敏：保留前6后4
                    Matcher idCardMatcher = ID_CARD_SIMPLE_PATTERN.matcher(masked);
                    sb = new StringBuffer();
                    while (idCardMatcher.find()) {
                        String idCard = idCardMatcher.group();
                        String maskedIdCard = idCard.substring(0, 6) + "********" + idCard.substring(14);
                        idCardMatcher.appendReplacement(sb, maskedIdCard);
                        modified = true;
                    }
                    idCardMatcher.appendTail(sb);
                    masked = sb.toString();
                    
                    // IP地址脱敏：保留前两段
                    Matcher ipMatcher = IP_PATTERN.matcher(masked);
                    sb = new StringBuffer();
                    while (ipMatcher.find()) {
                        String ip = ipMatcher.group();
                        String[] parts = ip.split("\\.");
                        if (parts.length == 4) {
                            String maskedIp = parts[0] + "." + parts[1] + ".*.*";
                            ipMatcher.appendReplacement(sb, maskedIp);
                            modified = true;
                        }
                    }
                    ipMatcher.appendTail(sb);
                    masked = sb.toString();
                    
                    // 银行卡脱敏：保留后4位
                    Matcher bankCardMatcher = BANK_CARD_PATTERN.matcher(masked);
                    sb = new StringBuffer();
                    while (bankCardMatcher.find()) {
                        String card = bankCardMatcher.group();
                        String maskedCard = "**** **** **** " + card.substring(card.length() - 4);
                        bankCardMatcher.appendReplacement(sb, maskedCard);
                        modified = true;
                    }
                    bankCardMatcher.appendTail(sb);
                    masked = sb.toString();
                    
                    return modified ? masked : s;
                });
                
                // 统计修改的记录数
                for (int i = 0; i < table.rowCount(); i++) {
                    String original = table.stringColumn(columnName).get(i);
                    String newValue = column.get(i);
                    if (original != null && !original.equals(newValue)) {
                        colMasked++;
                    }
                }
                
                if (colMasked > 0) {
                    report.addColumnStat(columnName + " (敏感数据)", colMasked);
                    totalMasked += colMasked;
                }
                
                table.replaceColumn(columnName, column);
            }
        }
        report.setMaskedSensitiveData(totalMasked);
        log.info("Masked {} sensitive data entries with advanced rules", totalMasked);
        return table;
    }

    // ==================== 5. 文本清洗 ====================
    
    public Table cleanText(Table table, CleaningReport report) {
        int totalCleaned = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colCleaned = 0;
                
                column = column.map(s -> {
                    if (s == null) return null;
                    String cleaned = s;
                    boolean modified = false;
                    
                    // 1. 去首尾空格
                    String trimmed = cleaned.trim();
                    if (!cleaned.equals(trimmed)) {
                        cleaned = trimmed;
                        modified = true;
                    }
                    
                    // 2. 移除特殊标记
                    String noSpecialMarks = SPECIAL_MARK_PATTERN.matcher(cleaned).replaceAll("");
                    if (!cleaned.equals(noSpecialMarks)) {
                        cleaned = noSpecialMarks;
                        modified = true;
                    }
                    
                    // 3. 错别字修正
                    String corrected = cleaned;
                    for (Map.Entry<String, String> entry : TYPO_CORRECTIONS.entrySet()) {
                        if (corrected.contains(entry.getKey())) {
                            corrected = corrected.replace(entry.getKey(), entry.getValue());
                            modified = true;
                        }
                    }
                    cleaned = corrected;
                    
                    // 4. 合并多个空格
                    String noMultipleSpaces = MULTIPLE_SPACES_PATTERN.matcher(cleaned).replaceAll(" ");
                    if (!cleaned.equals(noMultipleSpaces)) {
                        cleaned = noMultipleSpaces;
                        modified = true;
                    }
                    
                    // 5. 移除控制字符
                    String noControlChars = CONTROL_CHARS_PATTERN.matcher(cleaned).replaceAll("");
                    if (!cleaned.equals(noControlChars)) {
                        cleaned = noControlChars;
                        modified = true;
                    }
                    
                    // 6. 移除 HTML 标签
                    String noHtml = HTML_TAGS_PATTERN.matcher(cleaned).replaceAll("");
                    if (!cleaned.equals(noHtml)) {
                        cleaned = noHtml;
                        modified = true;
                    }
                    
                    // 7. 移除表情符号
                    String noEmoji = EMOJI_PATTERN.matcher(cleaned).replaceAll("");
                    if (!cleaned.equals(noEmoji)) {
                        cleaned = noEmoji;
                        modified = true;
                    }
                    
                    // 8. 邮箱统一转小写
                    if (columnName.toLowerCase().contains("email") || columnName.toLowerCase().contains("邮箱")) {
                        String lowercased = cleaned.toLowerCase();
                        if (!cleaned.equals(lowercased)) {
                            cleaned = lowercased;
                            modified = true;
                        }
                    }
                    
                    // 9. 再次去首尾空格
                    trimmed = cleaned.trim();
                    if (!cleaned.equals(trimmed)) {
                        cleaned = trimmed;
                        modified = true;
                    }
                    
                    return modified ? cleaned : s;
                });
                
                // 统计修改的记录数
                for (int i = 0; i < table.rowCount(); i++) {
                    String original = table.stringColumn(columnName).get(i);
                    String newValue = column.get(i);
                    if (original != null && !original.equals(newValue)) {
                        colCleaned++;
                    }
                }
                
                if (colCleaned > 0) {
                    report.addColumnStat(columnName + " (文本清洗)", colCleaned);
                    totalCleaned += colCleaned;
                }
                
                table.replaceColumn(columnName, column);
            }
        }
        report.setCleanedTextEntries(totalCleaned);
        log.info("Cleaned {} text entries with advanced rules", totalCleaned);
        return table;
    }

    // ==================== 6. 时间格式统一 ====================
    
    public Table standardizeDates(Table table, CleaningReport report) {
        int totalStandardized = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colStandardized = 0;
                
                column = column.map(s -> {
                    if (s == null || s.trim().isEmpty()) return s;
                    
                    String standardized = standardizeDateString(s.trim());
                    return standardized != null ? standardized : s;
                });
                
                // 统计修改的记录数
                for (int i = 0; i < table.rowCount(); i++) {
                    String original = table.stringColumn(columnName).get(i);
                    String newValue = column.get(i);
                    if (original != null && !original.equals(newValue)) {
                        colStandardized++;
                    }
                }
                
                if (colStandardized > 0) {
                    report.addColumnStat(columnName + " (日期标准化)", colStandardized);
                    totalStandardized += colStandardized;
                }
                
                table.replaceColumn(columnName, column);
            }
        }
        report.setStandardizedDates(totalStandardized);
        log.info("Standardized {} date entries to ISO 8601 format", totalStandardized);
        return table;
    }
    
    private String standardizeDateString(String dateStr) {
        // 格式1: 带时区的ISO时间格式 YYYY-MM-DDTHH:MM:SS+TZ
        Matcher isoTzMatcher = DATETIME_ISO_TZ_PATTERN.matcher(dateStr);
        if (isoTzMatcher.matches()) {
            return isoTzMatcher.group(1) + "-" + padWithZero(isoTzMatcher.group(2)) + "-" + padWithZero(isoTzMatcher.group(3)) + 
                   " " + padWithZero(isoTzMatcher.group(4)) + ":" + padWithZero(isoTzMatcher.group(5)) + ":" + padWithZero(isoTzMatcher.group(6));
        }
        
        // 格式2: YYYY/MM/DD HH:MM:SS 或 YYYY/MM/DD HH:MM
        Matcher dtSlashMatcher = DATETIME_SLASH_PATTERN.matcher(dateStr);
        if (dtSlashMatcher.matches()) {
            String second = dtSlashMatcher.group(6) != null ? padWithZero(dtSlashMatcher.group(6)) : "00";
            return dtSlashMatcher.group(1) + "-" + padWithZero(dtSlashMatcher.group(2)) + "-" + padWithZero(dtSlashMatcher.group(3)) + 
                   " " + padWithZero(dtSlashMatcher.group(4)) + ":" + padWithZero(dtSlashMatcher.group(5)) + ":" + second;
        }
        
        // 格式3: YYYY-MM-DD HH:MM:SS 或 YYYY-MM-DD HH:MM
        Matcher dtIsoMatcher = DATETIME_ISO_PATTERN.matcher(dateStr);
        if (dtIsoMatcher.matches()) {
            String second = dtIsoMatcher.group(6) != null ? padWithZero(dtIsoMatcher.group(6)) : "00";
            return dtIsoMatcher.group(1) + "-" + padWithZero(dtIsoMatcher.group(2)) + "-" + padWithZero(dtIsoMatcher.group(3)) + 
                   " " + padWithZero(dtIsoMatcher.group(4)) + ":" + padWithZero(dtIsoMatcher.group(5)) + ":" + second;
        }
        
        // 格式4: 中文日期格式 YYYY年MM月DD日
        Matcher chineseMatcher = DATE_CHINESE_PATTERN.matcher(dateStr);
        if (chineseMatcher.matches()) {
            return chineseMatcher.group(1) + "-" + padWithZero(chineseMatcher.group(2)) + "-" + padWithZero(chineseMatcher.group(3));
        }
        
        // 格式5: YYYY/MM/DD → YYYY-MM-DD
        Matcher slashMatcher = DATE_SLASH_PATTERN.matcher(dateStr);
        if (slashMatcher.matches()) {
            return slashMatcher.group(1) + "-" + padWithZero(slashMatcher.group(2)) + "-" + padWithZero(slashMatcher.group(3));
        }
        
        // 格式6: MM-DD-YYYY → YYYY-MM-DD
        Matcher dashMatcher = DATE_DASH_PATTERN.matcher(dateStr);
        if (dashMatcher.matches()) {
            return dashMatcher.group(3) + "-" + padWithZero(dashMatcher.group(1)) + "-" + padWithZero(dashMatcher.group(2));
        }
        
        // 格式7: 已经是 YYYY-MM-DD，补零
        Matcher isoMatcher = DATE_ISO_PATTERN.matcher(dateStr);
        if (isoMatcher.matches()) {
            String[] parts = dateStr.split("-");
            if (parts.length == 3) {
                return parts[0] + "-" + padWithZero(parts[1]) + "-" + padWithZero(parts[2]);
            }
        }
        
        // 格式8: 时间戳（秒或毫秒）
        Matcher tsMatcher = TIMESTAMP_PATTERN.matcher(dateStr);
        if (tsMatcher.matches()) {
            try {
                long ts = Long.parseLong(dateStr);
                // 简单处理：假设秒级时间戳，直接返回占位符
                if (dateStr.length() == 10) {
                    return "timestamp-" + dateStr;
                } else if (dateStr.length() == 13) {
                    return "timestamp-" + dateStr.substring(0, 10);
                }
            } catch (NumberFormatException e) {
                // 忽略
            }
        }
        
        return null;
    }
    
    private String padWithZero(String str) {
        return str.length() == 1 ? "0" + str : str;
    }

    // ==================== 7. 列名规范化 ====================
    
    public Table normalizeColumnNames(Table table) {
        Map<String, String> nameMapping = new HashMap<>();
        
        for (String originalName : table.columnNames()) {
            String normalized = normalizeColumnName(originalName);
            if (!originalName.equals(normalized)) {
                nameMapping.put(originalName, normalized);
            }
        }
        
        if (!nameMapping.isEmpty()) {
            for (Map.Entry<String, String> entry : nameMapping.entrySet()) {
                table.column(entry.getKey()).setName(entry.getValue());
            }
            log.info("Normalized {} column names", nameMapping.size());
        }
        
        return table;
    }
    
    private String normalizeColumnName(String name) {
        // 转小写
        String normalized = name.toLowerCase();
        
        // 空格转下划线
        normalized = normalized.replaceAll("\\s+", "_");
        
        // 去除特殊字符
        normalized = normalized.replaceAll("[^a-z0-9_]", "");
        
        return normalized;
    }

    // ==================== 8. 完整清洗流程 ====================
    
    public CleaningReport autoCleanWithReport(Table table) {
        CleaningReport report = new CleaningReport();
        Table result = table.copy();
        
        log.info("Starting advanced data cleaning pipeline...");
        
        // 按照知识库推荐顺序执行清洗
        // 1. 规范化列名
        result = normalizeColumnNames(result);
        
        // 2. 处理缺失值
        result = fillMissingValues(result, report);
        
        // 3. 去除重复
        result = removeDuplicates(result, report);
        
        // 4. 文本清洗
        result = cleanText(result, report);
        
        // 5. 敏感数据脱敏
        result = maskSensitiveData(result, report);
        
        // 6. 时间格式标准化
        result = standardizeDates(result, report);
        
        // 7. 异常值处理
        result = handleOutliers(result, report);
        
        report.setFinalRowCount(result.rowCount());
        report.setFinalTable(result);
        
        log.info("Advanced data cleaning completed. Original: {} rows, Final: {} rows", 
                report.getOriginalRowCount(), report.getFinalRowCount());
        
        return report;
    }

    // ==================== 9. 数据分析 ====================
    
    public Map<String, Object> analyzeData(Table table) {
        Map<String, Object> analysis = new HashMap<>();
        analysis.put("rowCount", table.rowCount());
        analysis.put("columnCount", table.columnCount());
        analysis.put("columns", table.columnNames());
        
        Map<String, Long> typeCount = new HashMap<>();
        Map<String, Map<String, Object>> columnDetails = new HashMap<>();
        
        for (String columnName : table.columnNames()) {
            String type = table.column(columnName).type().name();
            typeCount.put(type, typeCount.getOrDefault(type, 0L) + 1);
            
            Map<String, Object> details = new HashMap<>();
            details.put("type", type);
            
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn col = table.stringColumn(columnName);
                details.put("uniqueCount", col.unique().size());
                details.put("missingCount", col.countMissing());
            } else if (table.column(columnName) instanceof DoubleColumn) {
                DoubleColumn col = table.doubleColumn(columnName);
                details.put("mean", col.mean());
                details.put("min", col.min());
                details.put("max", col.max());
                details.put("missingCount", col.countMissing());
            }
            
            columnDetails.put(columnName, details);
        }
        
        analysis.put("columnTypes", typeCount);
        analysis.put("columnDetails", columnDetails);
        
        return analysis;
    }
}
