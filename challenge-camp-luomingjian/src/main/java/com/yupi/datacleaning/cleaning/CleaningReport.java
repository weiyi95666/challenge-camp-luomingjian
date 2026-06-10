package com.yupi.datacleaning.cleaning;

import lombok.Data;
import tech.tablesaw.api.Table;

import java.util.HashMap;
import java.util.Map;

@Data
public class CleaningReport {
    private int removedDuplicates = 0;
    private int standardizedDates = 0;
    private int filledMissingValues = 0;
    private int maskedSensitiveData = 0;
    private int cleanedTextEntries = 0;
    private int originalRowCount = 0;
    private int finalRowCount = 0;
    private Map<String, Integer> columnStats = new HashMap<>();
    private transient Table finalTable;
    
    public void addColumnStat(String columnName, int count) {
        columnStats.put(columnName, columnStats.getOrDefault(columnName, 0) + count);
    }
}
