package com.yupi.datacleaning.cleaning;

import tech.tablesaw.api.Table;
import tech.tablesaw.api.StringColumn;
import tech.tablesaw.api.DoubleColumn;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class DataCleaner {

    private static final Pattern PHONE_PATTERN = Pattern.compile("1[3-9]\\d{9}");
    private static final Pattern EMAIL_PATTERN = Pattern.compile("\\w+@\\w+\\.\\w+");
    private static final Pattern ID_CARD_PATTERN = Pattern.compile("\\d{17}[\\dXx]");
    private static final Pattern DATE_PATTERN = Pattern.compile("(\\d{4})[/-](\\d{1,2})[/-](\\d{1,2})");

    private CleaningReport report;

    public Table removeDuplicates(Table table) {
        int originalCount = table.rowCount();
        Table result = table.dropDuplicateRows();
        int removed = originalCount - result.rowCount();
        report.setRemovedDuplicates(removed);
        report.setOriginalRowCount(originalCount);
        log.info("Removed {} duplicate rows", removed);
        return result;
    }

    public Table maskSensitiveData(Table table) {
        int totalMasked = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colMasked = 0;
                column = column.map(s -> {
                    if (s == null) return null;
                    String masked = s;
                    int before = countMatches(PHONE_PATTERN, masked) + 
                                  countMatches(EMAIL_PATTERN, masked) + 
                                  countMatches(ID_CARD_PATTERN, masked);
                    
                    // 简单地替换敏感数据为固定的掩码
                    masked = PHONE_PATTERN.matcher(masked).replaceAll("1****");
                    masked = EMAIL_PATTERN.matcher(masked).replaceAll("****@***.com");
                    masked = ID_CARD_PATTERN.matcher(masked).replaceAll("****");
                    
                    int after = countMatches(PHONE_PATTERN, masked) + 
                                 countMatches(EMAIL_PATTERN, masked) + 
                                 countMatches(ID_CARD_PATTERN, masked);
                    
                    if (before > after) {
                        return masked;
                    }
                    return s;
                });
                
                // 统计这个列有多少条记录被修改
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
        log.info("Masked {} sensitive data entries", totalMasked);
        return table;
    }

    private int countMatches(Pattern pattern, String s) {
        if (s == null) return 0;
        Matcher matcher = pattern.matcher(s);
        int count = 0;
        while (matcher.find()) {
            count++;
        }
        return count;
    }

    public Table standardizeDates(Table table) {
        int totalStandardized = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colStandardized = 0;
                
                column = column.map(s -> {
                    if (s == null) return null;
                    if (DATE_PATTERN.matcher(s).find()) {
                        String result = s.replaceAll("(\\d{4})[/-](\\d{1,2})[/-](\\d{1,2})", "$1-$2-$3");
                        if (!s.equals(result)) {
                            return result;
                        }
                    }
                    return s;
                });
                
                // 统计这个列有多少条记录被修改
                for (int i = 0; i < table.rowCount(); i++) {
                    String original = table.stringColumn(columnName).get(i);
                    String newValue = column.get(i);
                    if (original != null && !original.equals(newValue)) {
                        colStandardized++;
                    }
                }
                
                if (colStandardized > 0) {
                    report.addColumnStat(columnName + " (日期)", colStandardized);
                    totalStandardized += colStandardized;
                }
                
                table.replaceColumn(columnName, column);
            }
        }
        report.setStandardizedDates(totalStandardized);
        log.info("Standardized {} date entries", totalStandardized);
        return table;
    }

    public Table fillMissingValues(Table table) {
        int totalFilled = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof DoubleColumn) {
                DoubleColumn column = table.doubleColumn(columnName);
                double mean = column.mean();
                int colFilled = 0;
                if (!Double.isNaN(mean)) {
                    for (int i = 0; i < column.size(); i++) {
                        if (Double.isNaN(column.getDouble(i))) {
                            colFilled++;
                        }
                    }
                }
                if (colFilled > 0) {
                    report.addColumnStat(columnName + " (数值)", colFilled);
                    totalFilled += colFilled;
                }
                
                if (!Double.isNaN(mean)) {
                    for (int i = 0; i < column.size(); i++) {
                        if (Double.isNaN(column.getDouble(i))) {
                            column.set(i, mean);
                        }
                    }
                    table.replaceColumn(columnName, column);
                }
            } else if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colFilled = 0;
                for (int i = 0; i < column.size(); i++) {
                    if (column.get(i) == null) {
                        colFilled++;
                    }
                }
                if (colFilled > 0) {
                    report.addColumnStat(columnName + " (文本)", colFilled);
                    totalFilled += colFilled;
                }
                
                for (int i = 0; i < column.size(); i++) {
                    if (column.get(i) == null) {
                        column.set(i, "");
                    }
                }
                table.replaceColumn(columnName, column);
            }
        }
        report.setFilledMissingValues(totalFilled);
        log.info("Filled {} missing values", totalFilled);
        return table;
    }

    public Table cleanText(Table table) {
        int totalCleaned = 0;
        for (String columnName : table.columnNames()) {
            if (table.column(columnName) instanceof StringColumn) {
                StringColumn column = table.stringColumn(columnName);
                int colCleaned = 0;
                
                column = column.map(s -> {
                    if (s == null) return null;
                    String trimmed = s.trim();
                    if (!s.equals(trimmed)) {
                        return trimmed;
                    }
                    return s;
                });
                
                // 统计这个列有多少条记录被修改
                for (int i = 0; i < table.rowCount(); i++) {
                    String original = table.stringColumn(columnName).get(i);
                    String newValue = column.get(i);
                    if (original != null && !original.equals(newValue)) {
                        colCleaned++;
                    }
                }
                
                if (colCleaned > 0) {
                    report.addColumnStat(columnName + " (文本)", colCleaned);
                    totalCleaned += colCleaned;
                }
                
                table.replaceColumn(columnName, column);
            }
        }
        report.setCleanedTextEntries(totalCleaned);
        log.info("Cleaned {} text entries", totalCleaned);
        return table;
    }

    public CleaningReport autoCleanWithReport(Table table) {
        report = new CleaningReport();
        Table result = table.copy();
        
        result = removeDuplicates(result);
        result = cleanText(result);
        result = maskSensitiveData(result);
        result = standardizeDates(result);
        result = fillMissingValues(result);
        
        report.setFinalRowCount(result.rowCount());
        
        // 保存结果到报告
        report.setFinalTable(result);
        
        return report;
    }

    public Map<String, Object> analyzeData(Table table) {
        Map<String, Object> analysis = new HashMap<>();
        analysis.put("rowCount", table.rowCount());
        analysis.put("columnCount", table.columnCount());
        analysis.put("columns", table.columnNames());
        
        Map<String, Long> typeCount = new HashMap<>();
        for (String column : table.columnNames()) {
            String type = table.column(column).type().name();
            typeCount.put(type, typeCount.getOrDefault(type, 0L) + 1);
        }
        analysis.put("columnTypes", typeCount);
        
        return analysis;
    }
}
