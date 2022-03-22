import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CartComponent } from './MyComponents/cart/cart.component';
import { LoginRegisterComponent } from './MyComponents/login-register/login-register.component';
import { PaymentComponent } from './MyComponents/payment/payment.component';
import { ProductComponent } from './MyComponents/product/product.component';
import { ShippingComponent } from './MyComponents/shipping/shipping.component';
import { SplashComponent } from './MyComponents/splash/splash.component';

const routes: Routes = [
  { path: 'login-register', component: LoginRegisterComponent },
  { path: '', component: SplashComponent },
  { path: 'cart', component: CartComponent },
  { path: 'product/:sku', component: ProductComponent },
  { path: 'shipping', component: ShippingComponent },
  { path: 'payment', component: PaymentComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
