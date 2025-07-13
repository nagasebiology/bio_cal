from datetime import datetime, timedelta
import calendar


class CalendarSVGGenerator:
    def __init__(self, cell_width=120, cell_height=100, header_height=40, margin=10):
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.header_height = header_height
        self.margin = margin
        self.week_days = ['月', '火', '水', '木', '金', '土', '日']
        
    def get_week_range(self, target_date):
        """指定された日付を含む週の月曜日から日曜日までの日付を取得"""
        # 月曜日を週の始まりとする（0=月曜日）
        days_since_monday = target_date.weekday()
        monday = target_date - timedelta(days=days_since_monday)
        
        week_dates = []
        for i in range(7):
            week_dates.append(monday + timedelta(days=i))
        
        return week_dates
    
    def get_four_week_range(self, today=None):
        """当日の週を含む4週間の日付範囲を取得（前1週間+当週+後2週間）"""
        if today is None:
            today = datetime.now().date()
        
        # 当日の週を取得
        current_week = self.get_week_range(today)
        
        # 前の週
        prev_week_start = current_week[0] - timedelta(days=7)
        prev_week = self.get_week_range(prev_week_start)
        
        # 後の2週間
        next_week1_start = current_week[0] + timedelta(days=7)
        next_week1 = self.get_week_range(next_week1_start)
        
        next_week2_start = current_week[0] + timedelta(days=14)
        next_week2 = self.get_week_range(next_week2_start)
        
        # 4週間分の日付をまとめる
        all_weeks = [prev_week, current_week, next_week1, next_week2]
        return all_weeks, today
    
    def generate_svg(self, output_file="calendar.svg", today=None):
        """4週間のカレンダーSVGを生成"""
        weeks, today_date = self.get_four_week_range(today)
        
        # SVGの全体サイズを計算
        total_width = 7 * self.cell_width + 2 * self.margin
        total_height = self.header_height + 4 * self.cell_height + 2 * self.margin  # ヘッダー行 + 4週間
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{total_width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <style>
            .header {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; text-anchor: middle; }}
            .date {{ font-family: Arial, sans-serif; font-size: 14px; text-anchor: middle; }}
            .month {{ font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; text-anchor: start; }}
            .day-number {{ font-family: Arial, sans-serif; font-size: 14px; text-anchor: end; }}
            .cell {{ fill: white; stroke: #cccccc; stroke-width: 1; }}
            .saturday {{ fill: #e3f2fd; }}
            .sunday {{ fill: #ffebee; }}
            .today {{ fill: #ffffa8; stroke: #cccccc; stroke-width: 1; }}
        </style>
    </defs>
    
    <!-- 背景 -->
    <rect width="{total_width}" height="{total_height}" fill="#fafafa"/>
'''
        
        # 曜日ヘッダーを描画
        y_offset = self.margin
        for i, day_name in enumerate(self.week_days):
            x = self.margin + i * self.cell_width
            svg_content += f'''
    <!-- 曜日ヘッダー: {day_name} -->
    <rect x="{x}" y="{y_offset}" width="{self.cell_width}" height="{self.header_height}" 
          class="cell" fill="#e0e0e0"/>
    <text x="{x + self.cell_width//2}" y="{y_offset + self.header_height//2 + 5}" 
          class="header">{day_name}</text>'''
        
        # 各週の日付を描画
        for week_idx, week in enumerate(weeks):
            y = self.margin + self.header_height + week_idx * self.cell_height
            
            for day_idx, date in enumerate(week):
                x = self.margin + day_idx * self.cell_width
                
                # セルのスタイルを決定
                cell_class = "cell"
                if date == today_date:
                    cell_class += " today"
                elif day_idx == 5:  # 土曜日
                    cell_class += " saturday"
                elif day_idx == 6:  # 日曜日
                    cell_class += " sunday"
                
                # 月表示の判定（毎月1日のみ）
                month_text = ""
                if date.day == 1:
                    month_text = f'<text x="{x + 8}" y="{y + 20}" class="month">{date.month}月</text>'
                
                svg_content += f'''
    <!-- {date.strftime('%Y-%m-%d')} -->
    <rect x="{x}" y="{y}" width="{self.cell_width}" height="{self.cell_height}" 
          class="{cell_class}"/>
    {month_text}
    <text x="{x + self.cell_width - 8}" y="{y + 20}" 
          class="day-number">{date.day}</text>'''
        
        svg_content += '''
</svg>'''
        
        # ファイルに書き込み
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        
        return output_file
    
    def print_date_info(self, today=None):
        """デバッグ用：日付情報を表示"""
        weeks, today_date = self.get_four_week_range(today)
        print(f"基準日: {today_date}")
        print(f"4週間の日付範囲:")
        
        for week_idx, week in enumerate(weeks):
            week_type = ["前週", "当週", "次週1", "次週2"][week_idx]
            print(f"  {week_type}: {week[0]} ～ {week[-1]}")


def main():
    """メイン関数"""
    generator = CalendarSVGGenerator()
    
    # カレンダーSVGを生成
    output_file = generator.generate_svg()
    print(f"カレンダーSVGを生成しました: {output_file}")
    
    # 日付情報を表示
    generator.print_date_info()


if __name__ == "__main__":
    main()