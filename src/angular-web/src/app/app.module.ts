import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { LoginRegisterComponent } from './MyComponents/login-register/login-register.component';
import { SplashComponent } from './MyComponents/splash/splash.component';
import { FormsModule } from '@angular/forms';
import { CartComponent } from './MyComponents/cart/cart.component';
import { ProductComponent } from './MyComponents/product/product.component';
import { ShippingComponent } from './MyComponents/shipping/shipping.component';
import { PaymentComponent } from './MyComponents/payment/payment.component';
import { HttpClientModule } from '@angular/common/http';
import { ReactiveFormsModule } from '@angular/forms';

@NgModule({
  declarations: [
    AppComponent,
    LoginRegisterComponent,
    SplashComponent,
    CartComponent,
    ProductComponent,
    ShippingComponent,
    PaymentComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    FormsModule,
    HttpClientModule,
    ReactiveFormsModule,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
