// ArkUI 特性测试文件
@Entry
@Component
struct MyComponent {
  @State message: string = 'Hello World';
  @Prop title: string;
  @Link count: number;
  @StorageLink('theme') theme: string = 'light';
  @Provide('data') data: any;
  @Consume('data') consumedData: any;
  @Watch('onMessageChange') watchedValue: string = '';
  
  // 样式函数
  @Styles
  cardStyle() {
    .width('100%')
    .height(100)
    .backgroundColor(Color.White)
  }
  
  // 扩展样式
  @Extend(Text)
  fancyText(color: Color) {
    .fontSize(20)
    .fontColor(color)
  }
  
  // 生命周期
  aboutToAppear() {
    console.log('Component is about to appear');
  }
  
  // 事件处理
  onMessageChange(oldValue: string, newValue: string) {
    console.log(`Message changed from ${oldValue} to ${newValue}`);
  }
  
  // 构建函数
  build() {
    Column() {
      Text(this.message)
        .fontSize(50)
        .fontWeight(FontWeight.Bold)
        .onClick(() => {
          this.message = 'Hello ArkUI';
        })
      
      Button('Click Me')
        .width('80%')
        .height(40)
        .onClick(this.handleClick.bind(this))
      
      Row() {
        Image($r('app.media.icon'))
          .width(50)
          .height(50)
      }
      .cardStyle()
    }
    .width('100%')
    .height('100%')
  }
  
  private handleClick() {
    this.count++;
  }
}

// 自定义组件
@Component
struct CustomButton {
  @Prop label: string = 'Button';
  private onClick: () => void;
  
  build() {
    Button(this.label)
      .onClick(() => {
        if (this.onClick) {
          this.onClick();
        }
      })
  }
}

// 预览
@Preview
struct PreviewComponent {
  build() {
    MyComponent({ title: 'Preview', count: 0 })
  }
}
