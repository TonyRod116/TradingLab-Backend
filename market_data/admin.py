from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Max, Min
from .models import HistoricalData, DataImportLog


@admin.register(HistoricalData)
class HistoricalDataAdmin(admin.ModelAdmin):
    list_display = [
        'symbol', 'timeframe', 'date', 'open_price', 'high_price', 
        'low_price', 'close_price', 'volume', 'is_bullish_display', 
        'price_change_display', 'created_at'
    ]
    
    list_filter = [
        'symbol', 'timeframe', 'date', 'created_at',
        ('date', admin.DateFieldListFilter),
    ]
    
    search_fields = ['symbol', 'date']
    
    readonly_fields = [
        'body_size', 'upper_shadow', 'lower_shadow', 
        'is_bullish', 'is_bearish', 'is_doji', 
        'price_change', 'price_change_percent', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('symbol', 'timeframe', 'date')
        }),
        ('OHLC Prices', {
            'fields': ('open_price', 'high_price', 'low_price', 'close_price')
        }),
        ('Volume', {
            'fields': ('volume',)
        }),
        ('Technical Analysis', {
            'fields': (
                'body_size', 'upper_shadow', 'lower_shadow',
                'is_bullish', 'is_bearish', 'is_doji',
                'price_change', 'price_change_percent'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    date_hierarchy = 'date'
    
    list_per_page = 100
    
    actions = ['calculate_statistics', 'export_to_csv']
    
    def is_bullish_display(self, obj):
        """Shows if candle is bullish with colors"""
        if obj.is_bullish:
            return format_html(
                '<span style="color: green; font-weight: bold;">🟢 Bullish</span>'
            )
        elif obj.is_bearish:
            return format_html(
                '<span style="color: red; font-weight: bold;">🔴 Bearish</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🟠 Doji</span>'
            )
    
    is_bullish_display.short_description = 'Candle Type'
    
    def price_change_display(self, obj):
        """Shows price change with colors"""
        change = obj.price_change
        if change > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">+${:.2f}</span>',
                change
            )
        elif change < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">-${:.2f}</span>',
                abs(change)
            )
        else:
            return format_html(
                '<span style="color: gray;">$0.00</span>'
            )
    
    price_change_display.short_description = 'Price Change'
    
    def calculate_statistics(self, request, queryset):
        """Action to calculate statistics for selected data"""
        if queryset.count() == 0:
            self.message_user(request, "No data selected for analysis.")
            return
        
        stats = queryset.aggregate(
            total_records=Count('id'),
            avg_open=Avg('open_price'),
            avg_high=Avg('high_price'),
            avg_low=Avg('low_price'),
            avg_close=Avg('close_price'),
            avg_volume=Avg('volume'),
            max_price=Max('high_price'),
            min_price=Min('low_price'),
            bullish_count=Count('id', filter={'close_price__gt': 'open_price'}),
            bearish_count=Count('id', filter={'close_price__lt': 'open_price'})
        )
        
        message = f"""
        Statistics for {stats['total_records']} records:
        - Average price: ${stats['avg_close']:.2f}
        - Highest price: ${stats['max_price']:.2f}
        - Lowest price: ${stats['min_price']:.2f}
        - Average volume: {stats['avg_volume']:.0f}
        - Bullish candles: {stats['bullish_count']}
        - Bearish candles: {stats['bearish_count']}
        """
        
        self.message_user(request, message)
    
    calculate_statistics.short_description = "Calculate statistics for selected data"
    
    def export_to_csv(self, request, queryset):
        """Action to export data to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="historical_data.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Symbol', 'Timeframe', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'
        ])
        
        for obj in queryset:
            writer.writerow([
                obj.symbol, obj.timeframe, obj.date,
                obj.open_price, obj.high_price, obj.low_price,
                obj.close_price, obj.volume
            ])
        
        return response
    
    export_to_csv.short_description = "Export selected data to CSV"


@admin.register(DataImportLog)
class DataImportLogAdmin(admin.ModelAdmin):
    list_display = [
        'file_name', 'symbol', 'timeframe', 'status', 'total_rows', 
        'imported_rows', 'skipped_rows', 'processing_time', 'created_at'
    ]
    
    list_filter = [
        'status', 'symbol', 'timeframe', 'created_at',
        ('created_at', admin.DateFieldListFilter),
    ]
    
    search_fields = ['file_name', 'symbol']
    
    readonly_fields = [
        'file_name', 'file_path', 'symbol', 'timeframe', 'total_rows',
        'imported_rows', 'skipped_rows', 'start_date', 'end_date',
        'status', 'error_message', 'processing_time', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Información del Archivo', {
            'fields': ('file_name', 'file_path', 'symbol', 'timeframe')
        }),
        ('Resultados de la Importación', {
            'fields': ('total_rows', 'imported_rows', 'skipped_rows')
        }),
        ('Rango de Fechas', {
            'fields': ('start_date', 'end_date')
        }),
        ('Estado y Errores', {
            'fields': ('status', 'error_message', 'processing_time')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    date_hierarchy = 'created_at'
    
    list_per_page = 50
    
    actions = ['retry_failed_imports', 'clean_old_logs']
    
    def retry_failed_imports(self, request, queryset):
        """Acción para reintentar importaciones fallidas"""
        failed_imports = queryset.filter(status='failed')
        count = failed_imports.count()
        
        if count == 0:
            self.message_user(request, "No hay importaciones fallidas para reintentar.")
            return
        
        # Aquí podrías implementar la lógica para reintentar
        self.message_user(
            request, 
            f"Se encontraron {count} importaciones fallidas. "
            "Implementa la lógica de reintento en el servicio."
        )
    
    retry_failed_imports.short_description = "Reintentar importaciones fallidas"
    
    def clean_old_logs(self, request, queryset):
        """Acción para limpiar logs antiguos"""
        from datetime import timedelta
        from django.utils import timezone
        
        # Eliminar logs de más de 30 días
        cutoff_date = timezone.now() - timedelta(days=30)
        old_logs = DataImportLog.objects.filter(created_at__lt=cutoff_date)
        count = old_logs.count()
        
        if count == 0:
            self.message_user(request, "No hay logs antiguos para limpiar.")
            return
        
        old_logs.delete()
        self.message_user(request, f"Se eliminaron {count} logs antiguos.")
    
    clean_old_logs.short_description = "Limpiar logs antiguos (más de 30 días)"
